# Create SDN Controller using Ryu framework
sdn_controller_code = '''"""
SDN Controller for IoT Network Policy Enforcement
Uses Ryu framework to manage OpenFlow switches and enforce access policies
"""
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp
import json
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import log_event
from config.config import *

class IoTSDNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(IoTSDNController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.device_policies = {}
        self.quarantined_devices = set()
        
        # Load existing policies from database
        self.load_device_policies()
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handle switch connection and install default flow"""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Install default flow to send unknown packets to controller
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
        print(f"Switch {datapath.id} connected")
    
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        """Add a flow entry to the switch"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        
        datapath.send_msg(mod)
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Handle incoming packets and enforce policies"""
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        
        dst = eth.dst
        src = eth.src
        
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        
        # Learn MAC address to avoid flooding next time
        self.mac_to_port[dpid][src] = in_port
        
        # Check if device is quarantined
        if src in self.quarantined_devices:
            self.redirect_to_honeypot(datapath, src, msg)
            return
        
        # Apply device-specific policies
        if src in self.device_policies:
            allowed = self.check_policy(pkt, src)
            if not allowed:
                self.log_policy_violation(src, dst)
                return  # Drop packet
        
        # Normal forwarding logic
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD
        
        actions = [parser.OFPActionOutput(out_port)]
        
        # Install flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
    
    def check_policy(self, pkt, src_mac):
        """Check if packet complies with device policy"""
        if src_mac not in self.device_policies:
            return True  # Allow if no policy defined
        
        policy = self.device_policies[src_mac]
        
        # Extract packet information
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        if not ipv4_pkt:
            return True  # Allow non-IP traffic
        
        dst_ip = ipv4_pkt.dst
        protocol = ipv4_pkt.proto
        
        # Get port information
        dst_port = None
        if protocol == 6:  # TCP
            tcp_pkt = pkt.get_protocol(tcp.tcp)
            if tcp_pkt:
                dst_port = tcp_pkt.dst_port
        elif protocol == 17:  # UDP
            udp_pkt = pkt.get_protocol(udp.udp)
            if udp_pkt:
                dst_port = udp_pkt.dst_port
        
        # Check against policy rules
        for rule in policy.get('rules', []):
            if self.match_rule(rule, dst_ip, dst_port, protocol):
                return rule.get('action') == 'allow'
        
        # Default deny
        return False
    
    def match_rule(self, rule, dst_ip, dst_port, protocol):
        """Check if packet matches policy rule"""
        # Simple IP matching (in production, implement CIDR matching)
        if 'dst_ip' in rule and rule['dst_ip'] != dst_ip:
            return False
        
        if 'dst_port' in rule and dst_port and rule['dst_port'] != dst_port:
            return False
        
        if 'protocol' in rule:
            rule_proto = {'TCP': 6, 'UDP': 17}.get(rule['protocol'], rule['protocol'])
            if rule_proto != protocol:
                return False
        
        return True
    
    def redirect_to_honeypot(self, datapath, src_mac, msg):
        """Redirect quarantined device traffic to honeypot"""
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        
        # Create flow to redirect all traffic from this device to honeypot
        match = parser.OFPMatch(eth_src=src_mac)
        
        # Modify destination IP to honeypot
        actions = [
            parser.OFPActionSetField(ipv4_dst=HONEYPOT_IP),
            parser.OFPActionOutput(ofproto.OFPP_NORMAL)
        ]
        
        # High priority flow to ensure redirection
        self.add_flow(datapath, 1000, match, actions)
        
        print(f"Redirecting traffic from {src_mac} to honeypot {HONEYPOT_IP}")
    
    def load_device_policies(self):
        """Load device policies from database"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT d.mac_address, p.policy_json
            FROM devices d
            JOIN policies p ON d.device_id = p.device_id
            WHERE p.active = TRUE
            """)
            
            for mac_address, policy_json in cursor.fetchall():
                policy = json.loads(policy_json)
                self.device_policies[mac_address] = policy
            
            conn.close()
            print(f"Loaded {len(self.device_policies)} device policies")
            
        except Exception as e:
            print(f"Error loading device policies: {e}")
    
    def quarantine_device(self, mac_address):
        """Add device to quarantine list"""
        self.quarantined_devices.add(mac_address)
        print(f"Device {mac_address} added to quarantine list")
    
    def unquarantine_device(self, mac_address):
        """Remove device from quarantine list"""
        self.quarantined_devices.discard(mac_address)
        print(f"Device {mac_address} removed from quarantine list")
    
    def log_policy_violation(self, src_mac, dst_ip):
        """Log policy violation event"""
        try:
            # Get device ID from MAC
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT device_id FROM devices WHERE mac_address = ?", (src_mac,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                device_id = result[0]
                log_event(DATABASE_PATH, device_id, 'POLICY_VIOLATION', 
                         f"Attempted connection to {dst_ip}", 'WARNING')
            
        except Exception as e:
            print(f"Error logging policy violation: {e}")

# Policy management functions
def create_device_policy(device_id, allowed_destinations):
    """Create network policy for a device based on learned behavior"""
    policy = {
        'device_id': device_id,
        'rules': []
    }
    
    # Create allow rules for learned destinations
    for dest in allowed_destinations:
        rule = {
            'action': 'allow',
            'dst_ip': dest['ip'],
            'dst_port': dest.get('port'),
            'protocol': dest.get('protocol', 'TCP')
        }
        policy['rules'].append(rule)
    
    # Add default deny rule
    policy['rules'].append({
        'action': 'deny',
        'description': 'Default deny all other traffic'
    })
    
    return policy

def install_device_policy(device_id, policy):
    """Install policy in database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Deactivate old policies
        cursor.execute("""
        UPDATE policies SET active = FALSE 
        WHERE device_id = ?
        """, (device_id,))
        
        # Insert new policy
        cursor.execute("""
        INSERT INTO policies (device_id, policy_json, active)
        VALUES (?, ?, TRUE)
        """, (device_id, json.dumps(policy)))
        
        conn.commit()
        conn.close()
        
        log_event(DATABASE_PATH, device_id, 'POLICY_CREATED', 
                 f"Network policy created with {len(policy['rules'])} rules")
        
        print(f"Policy installed for device {device_id}")
        
    except Exception as e:
        print(f"Error installing policy: {e}")
'''

with open(f"{project_name}/src/sdn_controller/iot_controller.py", "w") as f:
    f.write(sdn_controller_code)
    
print("Created SDN controller: src/sdn_controller/iot_controller.py")