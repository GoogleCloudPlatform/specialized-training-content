import React, { useState, useEffect, useRef } from 'react';
import { Stage, Layer, Rect, Text, Line, Group, Transformer } from 'react-konva';
import { nanoid } from 'nanoid';
import { Plus, Trash2, Edit2, ChevronRight, ChevronDown, MousePointer2, Download, Upload, X, FileJson, Focus, ZoomIn, ZoomOut, StickyNote, Link } from 'lucide-react';

export interface MindNode {
  id: string;
  text: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
  parentIds?: string[];
  color?: string;
  isCollapsed?: boolean;
  type?: 'node' | 'note';
}

const LEVEL_COLORS = [
  '#22c55e', // Level 0: Green
  '#f97316', // Level 1: Orange
  '#a855f7', // Level 2: Purple
  '#3b82f6', // Level 3: Blue
  '#db2777', // Level 4: Dark Pink
];

const EXTRA_COLORS = [
  '#06b6d4', // cyan
  '#84cc16', // lime
  '#eab308', // yellow
  '#6366f1', // indigo
  '#f43f5e', // rose
];

const getNodeLevel = (nodeId: string, allNodes: MindNode[], visited = new Set<string>()): number => {
  if (visited.has(nodeId)) return 0;
  visited.add(nodeId);
  
  const node = allNodes.find(n => n.id === nodeId);
  if (!node || !node.parentIds || node.parentIds.length === 0) return 0;
  
  const parentLevels = node.parentIds.map(pId => getNodeLevel(pId, allNodes, new Set(visited)));
  return Math.min(...parentLevels) + 1;
};

const getColorForLevel = (level: number): string => {
  if (level < LEVEL_COLORS.length) {
    return LEVEL_COLORS[level];
  }
  return EXTRA_COLORS[(level - LEVEL_COLORS.length) % EXTRA_COLORS.length];
};

const NODE_WIDTH = 140;
const NODE_HEIGHT = 50;
const MIN_NODE_WIDTH = 100;
const MIN_NODE_HEIGHT = 40;

export default function MindMap() {
  const [nodes, setNodes] = useState<MindNode[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showControls, setShowControls] = useState(true);
  const [editText, setEditText] = useState('');
  const [stageSize, setStageSize] = useState({ width: window.innerWidth, height: window.innerHeight });
  const [isToolbarVisible, setIsToolbarVisible] = useState(true);
  const [modal, setModal] = useState<{
    isOpen: boolean;
    type: 'prompt' | 'alert';
    title: string;
    message: string;
    value?: string;
    onConfirm?: (value?: string) => void;
  }>({
    isOpen: false,
    type: 'alert',
    title: '',
    message: '',
  });
  
  // Drag-to-connect state
  const [connectingFromId, setConnectingFromId] = useState<string | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  
  // Local File Persistence state
  const [currentMapName, setCurrentMapName] = useState('Untitled Map');
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const stageRef = useRef<any>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const shouldCenterRef = useRef(false);

  useEffect(() => {
    if (shouldCenterRef.current && nodes.length > 0) {
      centerView();
      shouldCenterRef.current = false;
    }
  }, [nodes]);

  useEffect(() => {
    const handleResize = () => {
      setStageSize({ width: window.innerWidth, height: window.innerHeight });
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleStageClick = (e: any) => {
    // If clicking on empty space
    if (e.target === e.target.getStage()) {
      if (nodes.length === 0) {
        const pos = e.target.getPointerPosition();
    const newNode: MindNode = {
      id: nanoid(),
      text: 'Main Concept',
      x: pos.x - NODE_WIDTH / 2,
      y: pos.y - NODE_HEIGHT / 2,
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
      parentIds: [],
      color: LEVEL_COLORS[0]
    };
        setNodes([newNode]);
        setSelectedId(newNode.id);
        startEditing(newNode.id, newNode.text);
      } else {
        setSelectedId(null);
        setEditingId(null);
      }
    }
  };

  const startEditing = (id: string, text: string) => {
    setEditingId(id);
    setEditText(text);
    // Use timeout to focus after render
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus();
        inputRef.current.select();
      }
    }, 50);
  };

  const handleNodeClick = (id: string) => {
    setSelectedId(id);
  };

  const handleNodeDblClick = (id: string, text: string) => {
    startEditing(id, text);
  };

  const addChild = (parentId: string) => {
    const parent = nodes.find(n => n.id === parentId);
    if (!parent) return;

    const level = getNodeLevel(parentId, nodes) + 1;
    const newNode: MindNode = {
      id: nanoid(),
      text: 'New Child',
      x: parent.x + (parent.width || NODE_WIDTH) + 60,
      y: parent.y + (Math.random() * 100 - 50),
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
      parentIds: [parentId],
      color: getColorForLevel(level),
      isCollapsed: false
    };

    // Ensure parent is expanded when adding a child
    setNodes(nodes.map(n => n.id === parentId ? { ...n, isCollapsed: false } : n).concat(newNode));
    setSelectedId(newNode.id);
    startEditing(newNode.id, newNode.text);
  };

  const addSibling = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (!node || !node.parentIds || node.parentIds.length === 0) return;

    const newNode: MindNode = {
      id: nanoid(),
      text: 'New Sibling',
      x: node.x,
      y: node.y + (node.height || NODE_HEIGHT) + 20,
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
      parentIds: [...node.parentIds],
      color: node.color
    };

    setNodes([...nodes, newNode]);
    setSelectedId(newNode.id);
    startEditing(newNode.id, newNode.text);
  };

  const addNote = () => {
    const stage = stageRef.current;
    const scale = stage.scaleX();
    const x = (stage.width() / 2 - stage.x()) / scale;
    const y = (stage.height() / 2 - stage.y()) / scale;

    const newNote: MindNode = {
      id: nanoid(),
      text: 'New Note',
      x: x - 100,
      y: y - 100,
      width: 200,
      height: 150,
      parentIds: [],
      type: 'note',
      color: '#fef08a' // yellow-200
    };

    setNodes([...nodes, newNote]);
    setSelectedId(newNote.id);
    startEditing(newNote.id, newNote.text);
  };

  const deleteNode = (id: string) => {
    // Recursive function to find nodes that should be deleted
    // A node is deleted if it loses its last parent
    const getNodesToPrune = (nodeId: string, nodesList: MindNode[]): string[] => {
      const toDelete = [nodeId];
      const children = nodesList.filter(n => n.parentIds?.includes(nodeId));
      
      children.forEach(child => {
        // If this child only has one parent (the one being deleted), it should also be deleted
        if (child.parentIds && child.parentIds.length === 1 && child.parentIds[0] === nodeId) {
          toDelete.push(...getNodesToPrune(child.id, nodesList));
        }
      });
      return toDelete;
    };

    const idsToDelete = getNodesToPrune(id, nodes);
    
    // For nodes NOT being deleted, remove the deleted node from their parentIds
    const updatedNodes = nodes
      .filter(n => !idsToDelete.includes(n.id))
      .map(n => ({
        ...n,
        parentIds: n.parentIds?.filter(pId => !idsToDelete.includes(pId))
      }));

    setNodes(updatedNodes);
    setSelectedId(null);
  };

  const updateNodeText = () => {
    if (editingId) {
      setNodes(nodes.map(n => n.id === editingId ? { ...n, text: editText } : n));
      setEditingId(null);
    }
  };

  const toggleCollapse = (id: string) => {
    setNodes(nodes.map(n => n.id === id ? { ...n, isCollapsed: !n.isCollapsed } : n));
  };

  const isNodeVisible = (nodeId: string, visited = new Set<string>()): boolean => {
    if (visited.has(nodeId)) return false;
    visited.add(nodeId);
    
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return false;
    if (node.type === 'note') return true;
    if (!node.parentIds || node.parentIds.length === 0) return true;
    
    // Visible if any parent is visible and not collapsed
    return node.parentIds.some(pId => {
      const parent = nodes.find(n => n.id === pId);
      return parent && !parent.isCollapsed && isNodeVisible(parent.id, new Set(visited));
    });
  };

  const isDescendant = (nodeId: string, potentialAncestorId: string, allNodes: MindNode[], visited = new Set<string>()): boolean => {
    if (visited.has(nodeId)) return false;
    visited.add(nodeId);
    
    const node = allNodes.find(n => n.id === nodeId);
    if (!node || !node.parentIds) return false;
    if (node.parentIds.includes(potentialAncestorId)) return true;
    return node.parentIds.some(pId => isDescendant(pId, potentialAncestorId, allNodes, new Set(visited)));
  };

  const handleDragEnd = (id: string, e: any) => {
    setNodes(nodes.map(n => n.id === id ? { ...n, x: e.target.x(), y: e.target.y() } : n));
  };

  const handleTransformEnd = (id: string, e: any) => {
    const node = e.target;
    const newWidth = Math.max(MIN_NODE_WIDTH, node.width() * node.scaleX());
    const newHeight = Math.max(MIN_NODE_HEIGHT, node.height() * node.scaleY());
    
    // Reset scale to 1 and update width/height
    node.setAttrs({
      width: newWidth,
      height: newHeight,
      scaleX: 1,
      scaleY: 1,
    });

    setNodes(nodes.map(n => n.id === id ? { 
      ...n, 
      x: node.x(), 
      y: node.y(),
      width: newWidth,
      height: newHeight
    } : n));
  };

  const handleStageMouseMove = (e: any) => {
    if (connectingFromId) {
      const stage = stageRef.current;
      const scale = stage.scaleX();
      const pointer = stage.getPointerPosition();
      setMousePos({
        x: (pointer.x - stage.x()) / scale,
        y: (pointer.y - stage.y()) / scale
      });
    }
  };

  const handleConnectStart = (id: string) => {
    setConnectingFromId(id);
    const node = nodes.find(n => n.id === id);
    if (node) {
      setMousePos({ x: node.x + (node.width || NODE_WIDTH), y: node.y + (node.height || NODE_HEIGHT) / 2 });
    }
  };

  const handleConnectEnd = (targetId: string) => {
    if (connectingFromId && connectingFromId !== targetId) {
      // Avoid cycles: check if targetId is an ancestor of connectingFromId
      if (isDescendant(connectingFromId, targetId, nodes)) {
        setModal({
          isOpen: true,
          type: 'alert',
          title: 'Cycle Detected',
          message: 'Cannot create a cycle in the mind map.',
        });
        setConnectingFromId(null);
        return;
      }

      setNodes(nodes.map(n => {
        if (n.id === targetId) {
          const currentParents = n.parentIds || [];
          if (!currentParents.includes(connectingFromId)) {
            return { ...n, parentIds: [...currentParents, connectingFromId] };
          }
        }
        return n;
      }));
    }
    setConnectingFromId(null);
  };
  const handleZoom = (direction: 'in' | 'out') => {
    const stage = stageRef.current;
    if (!stage) return;

    const scaleBy = 1.2;
    const oldScale = stage.scaleX();
    const newScale = direction === 'in' ? oldScale * scaleBy : oldScale / scaleBy;

    // Zoom towards center of screen
    const centerX = stage.width() / 2;
    const centerY = stage.height() / 2;

    const mousePointTo = {
      x: (centerX - stage.x()) / oldScale,
      y: (centerY - stage.y()) / oldScale,
    };

    stage.scale({ x: newScale, y: newScale });

    const newPos = {
      x: centerX - mousePointTo.x * newScale,
      y: centerY - mousePointTo.y * newScale,
    };
    stage.position(newPos);
    stage.batchDraw();
  };

  const handleWheel = (e: any) => {
    if (connectingFromId) return;
    e.evt.preventDefault();
    
    // Smoother zoom sensitivity
    const scaleBy = 1.05;
    const stage = stageRef.current;
    if (!stage) return;

    const oldScale = stage.scaleX();
    const pointer = stage.getPointerPosition();

    const mousePointTo = {
      x: (pointer.x - stage.x()) / oldScale,
      y: (pointer.y - stage.y()) / oldScale,
    };

    const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy;

    stage.scale({ x: newScale, y: newScale });

    const newPos = {
      x: pointer.x - mousePointTo.x * newScale,
      y: pointer.y - mousePointTo.y * newScale,
    };
    stage.position(newPos);
    stage.batchDraw();
  };

  const centerView = () => {
    const stage = stageRef.current;
    if (!stage || nodes.length === 0) return;

    // Find bounding box of visible nodes
    const visibleNodes = nodes.filter(n => isNodeVisible(n.id));
    if (visibleNodes.length === 0) return;

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    visibleNodes.forEach(node => {
      const w = node.width || NODE_WIDTH;
      const h = node.height || NODE_HEIGHT;
      minX = Math.min(minX, node.x);
      minY = Math.min(minY, node.y);
      maxX = Math.max(maxX, node.x + w);
      maxY = Math.max(maxY, node.y + h);
    });

    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;

    const stageWidth = stage.width();
    const stageHeight = stage.height();

    // Reset scale to 1 and center the bounding box
    stage.scale({ x: 1, y: 1 });
    stage.position({
      x: stageWidth / 2 - centerX,
      y: stageHeight / 2 - centerY
    });
    
    stage.batchDraw();
  };

  // File Persistence Functions
  const downloadMap = () => {
    setModal({
      isOpen: true,
      type: 'prompt',
      title: 'Download Map',
      message: 'Enter a name for your mind map:',
      value: currentMapName,
      onConfirm: (newName) => {
        const finalName = (newName || currentMapName).trim() || currentMapName;
        setCurrentMapName(finalName);

        const dataStr = JSON.stringify({
          version: '1.0',
          name: finalName,
          nodes: nodes
        }, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `${finalName.replace(/\s+/g, '_')}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
      }
    });
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const content = event.target?.result as string;
        const parsed = JSON.parse(content);
        
        if (parsed.nodes && Array.isArray(parsed.nodes)) {
          shouldCenterRef.current = true;
          setNodes(parsed.nodes);
          setCurrentMapName(parsed.name || 'Imported Map');
          setSelectedId(null);
        } else {
          setModal({
            isOpen: true,
            type: 'alert',
            title: 'Invalid File',
            message: 'Invalid mind map file format.',
          });
        }
      } catch (error) {
        setModal({
          isOpen: true,
          type: 'alert',
          title: 'Parse Error',
          message: 'Failed to parse the mind map file.',
        });
      }
    };
    reader.readAsText(file);
    // Reset input so the same file can be uploaded again
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const loadFromUrl = () => {
    setModal({
      isOpen: true,
      type: 'prompt',
      title: 'Load from URL',
      message: 'Enter the URL of a MindFlow JSON file:',
      value: '',
      onConfirm: async (url) => {
        if (!url) return;
        try {
          const response = await fetch(url);
          if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
          const parsed = await response.json();

          if (parsed.nodes && Array.isArray(parsed.nodes)) {
            shouldCenterRef.current = true;
            setNodes(parsed.nodes);
            setCurrentMapName(parsed.name || 'Remote Map');
            setSelectedId(null);
          } else {
            setModal({
              isOpen: true,
              type: 'alert',
              title: 'Invalid Format',
              message: 'The URL did not return a valid MindFlow JSON format.',
            });
          }
        } catch (error) {
          console.error('Fetch error:', error);
          setModal({
            isOpen: true,
            type: 'alert',
            title: 'Load Failed',
            message: `Failed to load from URL. This might be due to CORS restrictions or an invalid URL. Error: ${error instanceof Error ? error.message : String(error)}`,
          });
        }
      }
    });
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (editingId) return;

      if (e.key === 'Tab' && selectedId) {
        e.preventDefault();
        addChild(selectedId);
      }
      if (e.key === 'Enter' && selectedId) {
        e.preventDefault();
        addSibling(selectedId);
      }
      if ((e.key === 'Delete' || e.key === 'Backspace') && selectedId) {
        deleteNode(selectedId);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedId, editingId, nodes]);

  // Calculate absolute position for the input field
  const getEditingPos = () => {
    if (!editingId || !stageRef.current) return { x: 0, y: 0, scale: 1 };
    const node = nodes.find(n => n.id === editingId);
    if (!node) return { x: 0, y: 0, scale: 1 };
    
    const stage = stageRef.current;
    const scale = stage.scaleX();
    return {
      x: node.x * scale + stage.x(),
      y: node.y * scale + stage.y(),
      scale
    };
  };

  const editingPos = getEditingPos();

  return (
    <div className="relative w-full h-screen bg-zinc-50 overflow-hidden">
      {/* Toolbar */}
      {isToolbarVisible ? (
        <div className="absolute top-6 left-1/2 -translate-x-1/2 z-10 flex items-center gap-2 p-2 bg-white/80 backdrop-blur-md border border-zinc-200 rounded-2xl shadow-xl shadow-zinc-200/50 transition-all duration-300">
          <div className="px-4 py-1 border-r border-zinc-200 mr-2 flex items-center gap-2">
            <input
              type="text"
              value={currentMapName}
              onChange={(e) => setCurrentMapName(e.target.value)}
              className="text-sm font-semibold text-zinc-800 tracking-tight bg-transparent border-none focus:outline-none w-32"
              placeholder="Map Name"
            />
          </div>
          
          <div className="flex items-center gap-1 pr-2 border-r border-zinc-200">
            <button 
              onClick={addNote}
              className="p-1.5 text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
              title="Add Sticky Note"
            >
              <StickyNote size={16} />
            </button>
            <button 
              onClick={downloadMap}
              className="p-1.5 text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
              title="Download Map (.json)"
            >
              <Download size={16} />
            </button>
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="p-1.5 text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
              title="Upload Map (.json)"
            >
              <Upload size={16} />
            </button>
            <button 
              onClick={loadFromUrl}
              className="p-1.5 text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
              title="Load from URL"
            >
              <Link size={16} />
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".json"
              className="hidden"
            />
          </div>

          {selectedId ? (
            <>
              <button 
                onClick={() => addChild(selectedId)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-100 rounded-lg transition-colors"
                title="Add Child (Tab)"
              >
                <Plus size={14} />
                Child
              </button>
              {nodes.find(n => n.id === selectedId)?.parentIds?.length && (
                <button 
                  onClick={() => addSibling(selectedId)}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-100 rounded-lg transition-colors"
                  title="Add Sibling (Enter)"
                >
                  <ChevronDown size={14} />
                  Sibling
                </button>
              )}
              <button 
                onClick={() => {
                  const node = nodes.find(n => n.id === selectedId);
                  if (node) startEditing(node.id, node.text);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-100 rounded-lg transition-colors"
              >
                <Edit2 size={14} />
                Edit
              </button>
              <button 
                onClick={() => deleteNode(selectedId)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                <Trash2 size={14} />
                Delete
              </button>
            </>
          ) : (
            <div className="px-4 py-1.5 text-xs text-zinc-500 font-medium flex items-center gap-2">
              <MousePointer2 size={14} />
              {nodes.length === 0 ? "Click anywhere to start" : "Select a node to edit"}
            </div>
          )}

          <div className="w-px h-4 bg-zinc-200 mx-1" />
          
          <button 
            onClick={() => setIsToolbarVisible(false)}
            className="p-1.5 text-zinc-500 hover:bg-zinc-100 rounded-lg transition-colors"
            title="Collapse Toolbar"
          >
            <ChevronDown className="rotate-180" size={16} />
          </button>
        </div>
      ) : (
        <button 
          onClick={() => setIsToolbarVisible(true)}
          className="absolute top-6 left-1/2 -translate-x-1/2 z-10 p-2 bg-white/80 backdrop-blur-md border border-zinc-200 rounded-full shadow-lg text-zinc-500 hover:text-zinc-800 transition-all"
          title="Expand Toolbar"
        >
          <ChevronDown size={18} />
        </button>
      )}

      {/* Canvas */}
      <Stage 
        width={stageSize.width} 
        height={stageSize.height} 
        onClick={handleStageClick}
        onMouseMove={handleStageMouseMove}
        onMouseUp={() => setConnectingFromId(null)}
        onWheel={handleWheel}
        ref={stageRef}
        draggable={!editingId && !connectingFromId}
      >
        <Layer>
          {/* Connections */}
          {nodes.filter(n => isNodeVisible(n.id)).map(node => {
            if (!node.parentIds || node.parentIds.length === 0) return null;
            
            return node.parentIds.map(pId => {
              const parent = nodes.find(n => n.id === pId);
              if (!parent || parent.isCollapsed) return null;

              const nodeWidth = node.width || NODE_WIDTH;
              const nodeHeight = node.height || NODE_HEIGHT;
              const parentWidth = parent.width || NODE_WIDTH;
              const parentHeight = parent.height || NODE_HEIGHT;

              // Calculate connection points
              const isChildToRight = node.x > parent.x;
              
              const startX = isChildToRight ? parent.x + parentWidth : parent.x;
              const startY = parent.y + parentHeight / 2;
              const endX = isChildToRight ? node.x : node.x + nodeWidth;
              const endY = node.y + nodeHeight / 2;
              
              const cp1x = startX + (endX - startX) * 0.5;
              const cp1y = startY;
              const cp2x = startX + (endX - startX) * 0.5;
              const cp2y = endY;
              
              return (
                <Line
                  key={`line-${node.id}-${pId}`}
                  points={[startX, startY, cp1x, cp1y, cp2x, cp2y, endX, endY]}
                  stroke={node.color || '#cbd5e1'}
                  strokeWidth={2}
                  opacity={0.6}
                  bezier={true}
                />
              );
            });
          })}

          {/* Temporary Connection Line */}
          {connectingFromId && (
            <Line
              points={[
                nodes.find(n => n.id === connectingFromId)!.x + (nodes.find(n => n.id === connectingFromId)!.width || NODE_WIDTH),
                nodes.find(n => n.id === connectingFromId)!.y + (nodes.find(n => n.id === connectingFromId)!.height || NODE_HEIGHT) / 2,
                mousePos.x,
                mousePos.y
              ]}
              stroke="#3b82f6"
              strokeWidth={2}
              dash={[5, 5]}
            />
          )}

          {/* Nodes */}
          {nodes.filter(n => isNodeVisible(n.id)).map(node => {
            const hasChildren = nodes.some(n => n.parentIds?.includes(node.id));
            const nodeWidth = node.width || NODE_WIDTH;
            const nodeHeight = node.height || NODE_HEIGHT;
            
            const isNote = node.type === 'note';
            
            return (
              <React.Fragment key={node.id}>
                <Group
                  x={node.x}
                  y={node.y}
                  width={nodeWidth}
                  height={nodeHeight}
                  draggable={!editingId && !connectingFromId}
                  onDragEnd={(e) => handleDragEnd(node.id, e)}
                  onTransformEnd={(e) => handleTransformEnd(node.id, e)}
                  onClick={(e) => {
                    e.cancelBubble = true;
                    handleNodeClick(node.id);
                  }}
                  onDblClick={(e) => {
                    e.cancelBubble = true;
                    handleNodeDblClick(node.id, node.text);
                  }}
                  onMouseUp={(e) => {
                    if (connectingFromId && !isNote) {
                      e.cancelBubble = true;
                      handleConnectEnd(node.id);
                    }
                  }}
                  name="node-group"
                  id={node.id}
                >
                  <Rect
                    width={nodeWidth}
                    height={nodeHeight}
                    fill={isNote ? '#fef08a' : 'white'}
                    stroke={selectedId === node.id ? (isNote ? '#facc15' : (node.color || '#3b82f6')) : (isNote ? '#fef08a' : '#e2e8f0')}
                    strokeWidth={selectedId === node.id ? 2 : 1}
                    cornerRadius={isNote ? 2 : 8}
                    shadowBlur={selectedId === node.id ? 12 : 2}
                    shadowColor="#000000"
                    shadowOpacity={0.08}
                    shadowOffset={{ x: 0, y: 3 }}
                  />
                  {!isNote && (
                    <Rect 
                      width={4}
                      height={nodeHeight}
                      fill={node.color || '#3b82f6'}
                      cornerRadius={[8, 0, 0, 8]}
                    />
                  )}
                  <Text
                    text={node.text}
                    width={nodeWidth}
                    height={nodeHeight}
                    align={isNote ? "left" : "center"}
                    verticalAlign={isNote ? "top" : "middle"}
                    fontSize={isNote ? 12 : 13}
                    fontFamily={isNote ? "Inter" : "Inter"}
                    fontStyle={isNote ? "normal" : "500"}
                    padding={10}
                    fill="#18181b"
                    wrap="word"
                  />
                  
                  {/* Connection Handle */}
                  {!isNote && (
                    <Group
                      x={nodeWidth}
                      y={nodeHeight / 2}
                      onMouseDown={(e) => {
                        e.cancelBubble = true;
                        handleConnectStart(node.id);
                      }}
                      onMouseUp={(e) => {
                        e.cancelBubble = true;
                        handleConnectEnd(node.id);
                      }}
                    >
                      <Rect
                        x={-4}
                        y={-10}
                        width={12}
                        height={20}
                        fill="transparent"
                      />
                      <Rect
                        x={0}
                        y={-6}
                        width={4}
                        height={12}
                        fill={node.color || '#3b82f6'}
                        cornerRadius={2}
                        opacity={0.5}
                      />
                    </Group>
                  )}

                  {/* Collapse/Expand Toggle */}
                  {hasChildren && !isNote && (
                    <Group
                      x={nodeWidth - 10}
                      y={nodeHeight / 2}
                      onClick={(e) => {
                        e.cancelBubble = true;
                        toggleCollapse(node.id);
                      }}
                    >
                      <Rect
                        x={-6}
                        y={-6}
                        width={12}
                        height={12}
                        fill="white"
                        stroke={node.color || '#3b82f6'}
                        strokeWidth={1}
                        cornerRadius={6}
                      />
                      <Text
                        text={node.isCollapsed ? '+' : '-'}
                        x={-3}
                        y={-5}
                        fontSize={10}
                        fontFamily="monospace"
                        fill={node.color || '#3b82f6'}
                        fontStyle="bold"
                      />
                    </Group>
                  )}
                </Group>
                {selectedId === node.id && !editingId && (
                  <Transformer
                    anchorSize={6}
                    borderDash={[6, 2]}
                    rotateEnabled={false}
                    boundBoxFunc={(oldBox, newBox) => {
                      if (newBox.width < MIN_NODE_WIDTH || newBox.height < MIN_NODE_HEIGHT) {
                        return oldBox;
                      }
                      return newBox;
                    }}
                    nodes={[stageRef.current?.findOne(`#${node.id}`)]}
                  />
                )}
              </React.Fragment>
            );
          })}
        </Layer>
      </Stage>

      {/* Floating Input for Editing */}
      {editingId && (
        <div 
          className="absolute z-20 pointer-events-none"
          style={{
            left: editingPos.x,
            top: editingPos.y,
            width: (nodes.find(n => n.id === editingId)?.width || NODE_WIDTH) * editingPos.scale,
            height: (nodes.find(n => n.id === editingId)?.height || NODE_HEIGHT) * editingPos.scale,
          }}
        >
          <textarea
            ref={inputRef}
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            onBlur={updateNodeText}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                updateNodeText();
              }
              if (e.key === 'Escape') setEditingId(null);
            }}
            className="w-full h-full px-3 py-2 text-sm font-medium text-zinc-900 bg-white border-2 border-blue-500 rounded-lg shadow-lg focus:outline-none pointer-events-auto resize-none"
            style={{ fontSize: `${13 * editingPos.scale}px` }}
          />
        </div>
      )}

      {/* Legend / Instructions */}
      <div className="absolute bottom-6 right-6 flex flex-col items-end gap-2">
        <div className="flex gap-2">
          <div className="flex bg-white/80 backdrop-blur-md border border-zinc-200 rounded-full shadow-lg overflow-hidden">
            <button 
              onClick={() => handleZoom('in')}
              className="p-2 text-zinc-500 hover:text-zinc-800 hover:bg-zinc-100 transition-all border-r border-zinc-200"
              title="Zoom In"
            >
              <ZoomIn size={18} />
            </button>
            <button 
              onClick={() => handleZoom('out')}
              className="p-2 text-zinc-500 hover:text-zinc-800 hover:bg-zinc-100 transition-all"
              title="Zoom Out"
            >
              <ZoomOut size={18} />
            </button>
          </div>
          <button 
            onClick={centerView}
            className="p-2 bg-white/80 backdrop-blur-md border border-zinc-200 rounded-full shadow-lg text-zinc-500 hover:text-zinc-800 transition-all"
            title="Center View"
          >
            <Focus size={18} />
          </button>
          <button 
            onClick={() => setShowControls(!showControls)}
            className="p-2 bg-white/80 backdrop-blur-md border border-zinc-200 rounded-full shadow-lg text-zinc-500 hover:text-zinc-800 transition-all"
            title={showControls ? "Hide Controls" : "Show Controls"}
          >
            {showControls ? <ChevronDown size={18} /> : <ChevronRight className="rotate-180" size={18} />}
          </button>
        </div>
        
        {showControls && (
          <div className="p-4 bg-white/80 backdrop-blur-md border border-zinc-200 rounded-xl shadow-lg text-[11px] text-zinc-500 space-y-1">
            <p className="font-semibold text-zinc-700 mb-1 uppercase tracking-wider">Controls</p>
            <p>• Double-click node to edit text</p>
            <p>• Drag nodes to reposition</p>
            <p>• Drag background to pan</p>
            <p>• Scroll to zoom</p>
            <p>• <span className="font-mono bg-zinc-100 px-1 rounded text-zinc-600">Tab</span>: Add child</p>
            <p>• <span className="font-mono bg-zinc-100 px-1 rounded text-zinc-600">Enter</span>: Add sibling (or save text)</p>
            <p>• <span className="font-mono bg-zinc-100 px-1 rounded text-zinc-600">Shift + Enter</span>: New line in node</p>
            <p>• <span className="font-mono bg-zinc-100 px-1 rounded text-zinc-600">Del</span>: Delete node</p>
            <p>• <b>Drag handle</b> (right side) to connect nodes</p>
          </div>
        )}
      </div>

      {/* Custom Modal */}
      {modal.isOpen && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-[2px]">
          <div className="bg-white rounded-2xl shadow-2xl border border-zinc-200 w-full max-w-sm overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-zinc-900 mb-2">{modal.title}</h3>
              <p className="text-sm text-zinc-500 mb-4">{modal.message}</p>
              
              {modal.type === 'prompt' && (
                <input
                  type="text"
                  value={modal.value}
                  onChange={(e) => setModal({ ...modal, value: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-50 border border-zinc-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all mb-4"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      modal.onConfirm?.(modal.value);
                      setModal({ ...modal, isOpen: false });
                    }
                    if (e.key === 'Escape') {
                      setModal({ ...modal, isOpen: false });
                    }
                  }}
                />
              )}
              
              <div className="flex justify-end gap-2">
                {modal.type === 'prompt' && (
                  <button
                    onClick={() => setModal({ ...modal, isOpen: false })}
                    className="px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 rounded-xl transition-all"
                  >
                    Cancel
                  </button>
                )}
                <button
                  onClick={() => {
                    modal.onConfirm?.(modal.value);
                    setModal({ ...modal, isOpen: false });
                  }}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-lg shadow-blue-600/20 transition-all"
                >
                  {modal.type === 'prompt' ? 'Confirm' : 'OK'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
