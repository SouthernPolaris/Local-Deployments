import { useCallback, useEffect } from 'react';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  useNodesState, 
  useEdgesState, 
  addEdge,
  type Connection, 
  type Edge,       
  type Node        
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import axios from 'axios';

interface VMNodeData extends Record<string, unknown> {
  label: string;
}

const FIXED_MASTER_ID = "00000000-0000-0000-0000-000000000001"; 

export default function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<VMNodeData>>([
    { 
      id: FIXED_MASTER_ID, 
      position: { x: 0, y: 0 }, 
      data: { label: 'Jumpbox', role: 'jumpbox_main' }, 
      type: 'input' 
    },
  ]);
  
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)), 
    [setEdges]
  );

  const onEdgeUpdate = useCallback(
    (oldEdge: Edge, newConnection: Connection) => {
      setEdges((els) => {
        const filtered = els.filter((e) => e.id !== oldEdge.id);
        return addEdge(newConnection, filtered);
      });
    },
    [setEdges]
  );

  const deleteSelected = useCallback(() => {
    setNodes((nds) => nds.filter((node) => !node.selected));
    setEdges((eds) => eds.filter((edge) => !edge.selected));
  }, [setNodes, setEdges]);

  const addNode = (role: 'service' | 'jumpbox_local') => {
    const newNode: Node<VMNodeData> = {
      id: crypto.randomUUID(),
      position: { x: Math.random() * 400, y: Math.random() * 400 },
      data: { label: `${role.toUpperCase()} ${nodes.length + 1}`, role: role },
      style: { 
        background: role === 'service' ? '#d9f7be' : '#bae7ff',
        border: '1px solid #777',
        borderRadius: '5px'
      } 
    };
    setNodes((nds) => nds.concat(newNode));
  };

  const deploy = async () => {
    const payload = {
      range_metadata: { id: FIXED_MASTER_ID, name: "Cyber-Lab" },
      nodes: nodes.map((n: Node<VMNodeData>) => ({ 
        id: n.id, 
        label: n.data.label, 
        template_id: 1001, 
        role: n.data.role || (n.id === FIXED_MASTER_ID ? 'jumpbox_main' : 'service'),
        position: n.position 
      })),
      links: edges.map((e: Edge) => ({ 
        source: e.source, 
        target: e.target,
        connection_type: "vlan_bridge" 
      }))
    };
    
    try {
      await axios.post('http://localhost:8000/api/v1/range', payload);
      alert("Deployment logic triggered! Check backend logs.");
    } catch (error: any) {
      console.error("API Error:", error.response?.data || error.message);
    }
  };

  // Restore state on load
  useEffect(() => {
    const loadState = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/v1/ranges');
        const myLab = res.data.find((r: any) => r.metadata.id === FIXED_MASTER_ID);

        if (myLab) {
          console.log("Restoring previous topology...");
          setNodes(myLab.nodes.map((n: any) => ({
            id: n.id,
            position: n.position || { x: 0, y: 0 },
            data: { label: n.label, role: n.role },
            style: { 
                background: n.role === 'service' ? '#d9f7be' : '#bae7ff',
                // Restore visual style if needed
            },
            type: n.role === 'jumpbox_main' ? 'input' : 'default'
          })));

          setEdges(myLab.links.map((l: any) => ({
            id: `e-${l.source}-${l.target}`,
            source: l.source,
            target: l.target
          })));
        }
      } catch (e) {
        console.error("Failed to load state:", e);
      }
    };

    loadState();
  }, [setNodes, setEdges]);

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#f0f2f5' }}>
      {}
      <div style={{ position: 'absolute', zIndex: 10, top: 20, left: 20}}>
         <button onClick={() => addNode('service')}>+ Add Service VM</button>
         <button onClick={() => addNode('jumpbox_local')}>+ Add Local Jumpbox</button>
         <hr />
         <button onClick={deleteSelected} style={{ background: '#ff7875', color: 'white' }}>Delete Selected</button>
         <button onClick={deploy} style={{ background: '#1890ff', color: 'white' }}>Deploy to Proxmox</button>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        deleteKeyCode={['Backspace', 'Delete']}
        fitView
      >
        <Background color="#ccc" variant={"dots" as any} />
        <Controls />
      </ReactFlow>
    </div>
  );
}