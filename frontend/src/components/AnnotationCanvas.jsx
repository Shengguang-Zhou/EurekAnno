import React, { useEffect, useState, useRef } from 'react';
import { Stage, Layer, Rect, Image as KonvaImage, Group, Text, Tag, Label, Line, Transformer } from 'react-konva';
import { Box, Paper, Skeleton, Typography, useTheme, IconButton, Tooltip, Menu, MenuItem, ListItemIcon, ListItemText, Chip } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PanToolIcon from '@mui/icons-material/PanTool';
import BrushIcon from '@mui/icons-material/Brush';
import CenterFocusStrongIcon from '@mui/icons-material/CenterFocusStrong';
import ClassIcon from '@mui/icons-material/Category';
import useImage from 'use-image';
import { useApp, DETECTION_MODES } from '../context/AppContext';

/**
 * Helper: generate distinct colors for classes
 */
function generateColors(count) {
  const colors = [];
  let i = 0;
  while (i < count) {
    const hue = (i * 137.5) % 360; // golden angle
    colors.push(`hsl(${hue}, 70%, 60%)`);
    i += 1;
  }
  return colors;
}

/**
 * Compute local (relative) points for mask so it can be displayed within
 * a group whose top-left corner is the bounding box. For each point (x, y),
 * offset by boxX, boxY to align the mask with the bounding box in local coords.
 */
function getLocalMaskPoints(maskPoints, boxX, boxY) {
  const localPoints = [];
  for (let i = 0; i < maskPoints.length; i++) {
    const px = maskPoints[i][0] - boxX;
    const py = maskPoints[i][1] - boxY;
    localPoints.push([px, py]);
  }
  // Flatten for Konva <Line points> array: [x1,y1, x2,y2, ...]
  return localPoints.flat();
}

/**
 * Convert normalized [x1, y1, x2, y2] to absolute pixel coords
 */
function denormalizeBbox(bbox, imgW, imgH) {
  return {
    x: bbox[0] * imgW,
    y: bbox[1] * imgH,
    width: (bbox[2] - bbox[0]) * imgW,
    height: (bbox[3] - bbox[1]) * imgH,
  };
}

/**
 * Given the bounding box and the mask in absolute coordinates,
 * shift them by dx, dy. Then return the updated bounding box & mask.
 */
function shiftBboxAndMask(obj, dx, dy, imgW, imgH) {
  // Bbox
  const bX1 = obj.bbox[0] * imgW + dx;
  const bY1 = obj.bbox[1] * imgH + dy;
  const bX2 = obj.bbox[2] * imgW + dx;
  const bY2 = obj.bbox[3] * imgH + dy;

  // Normalize new coords
  const nbbox = [
    bX1 / imgW,
    bY1 / imgH,
    bX2 / imgW,
    bY2 / imgH,
  ];

  // Mask shift if present
  let nmask = null;
  if (obj.mask && Array.isArray(obj.mask)) {
    nmask = obj.mask.map(pt => [pt[0] + dx, pt[1] + dy]);
  }

  return { nbbox, nmask };
}

/**
 * Scale bounding box around top-left corner of the rect.
 * We'll apply rect's scaleX, scaleY to the width/height.
 * Also scale the mask points relative to the bounding box top-left.
 */
function scaleBboxAndMask(obj, scaleX, scaleY, anchorX, anchorY, imgW, imgH) {
  // Denormalize
  const absX1 = obj.bbox[0] * imgW;
  const absY1 = obj.bbox[1] * imgH;
  const absW = (obj.bbox[2] - obj.bbox[0]) * imgW;
  const absH = (obj.bbox[3] - obj.bbox[1]) * imgH;

  // New width/height
  const newW = absW * scaleX;
  const newH = absH * scaleY;

  // Bbox in absolute coords
  const bX2 = absX1 + newW;
  const bY2 = absY1 + newH;

  // Normalize
  const nbbox = [
    absX1 / imgW,
    absY1 / imgH,
    bX2 / imgW,
    bY2 / imgH,
  ];

  // Mask scale
  let nmask = null;
  if (obj.mask && Array.isArray(obj.mask)) {
    // Each point is scaled around (absX1, absY1).
    nmask = obj.mask.map(pt => {
      const localX = pt[0] - absX1;
      const localY = pt[1] - absY1;
      return [
        absX1 + localX * scaleX,
        absY1 + localY * scaleY,
      ];
    });
  }

  return { nbbox, nmask };
}

// Enum for editing modes
const EDIT_MODES = {
  SELECT: 'select',
  DRAW: 'draw',
  PAN: 'pan'
};

const AnnotationCanvas = () => {
  const theme = useTheme();
  const {
    currentImage,
    detectionMode,
    imagePrompts,
    updateImagePrompts,
    currentResults,
    hiddenObjects,
    updateImageDimensions,
    addBboxToResults,
    updateBboxInResults,
    removeBboxFromResults,
    updateObjectClass,
    setIsLoading,
    setError,
  } = useApp();

  const [image, imageStatus] = useImage(currentImage?.url || '');
  const [scale, setScale] = useState(1);
  const [stageSize, setStageSize] = useState({ width: 0, height: 0 });
  const [drawing, setDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState({ x: 0, y: 0 });
  const [currentBox, setCurrentBox] = useState(null);
  const [hoveredObject, setHoveredObject] = useState(null);
  const [selectedObjectIndex, setSelectedObjectIndex] = useState(null);
  const [selectedShapeRef, setSelectedShapeRef] = useState(null);
  const [editMode, setEditMode] = useState(EDIT_MODES.SELECT);
  const [stagePosition, setStagePosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);

  // Add state for class menu
  const [classMenuAnchor, setClassMenuAnchor] = useState(null);
  const classMenuOpen = Boolean(classMenuAnchor);

  const containerRef = useRef(null);
  const stageRef = useRef(null);
  const transformerRef = useRef(null);
  const layerRef = useRef(null);

  /**
   * When the image is loaded, compute scaling to fit inside container
   */
  useEffect(() => {
    if (!image || !containerRef.current) return;
    const container = containerRef.current;
    const cW = container.offsetWidth;
    const cH = container.offsetHeight;
    const sX = cW / image.width;
    const sY = cH / image.height;
    const newScale = Math.min(sX, sY, 1);
    setScale(newScale);
    setStageSize({
      width: image.width * newScale,
      height: image.height * newScale,
    });
    if (currentImage && (currentImage.width === 0 || currentImage.height === 0)) {
      updateImageDimensions(currentImage.id, image.width, image.height);
    }
    // Reset stage position when image changes
    setStagePosition({ x: 0, y: 0 });
    setSelectedObjectIndex(null); // Deselect when image changes
    setSelectedShapeRef(null);
    
    setEditMode(EDIT_MODES.SELECT);
  }, [image, currentImage, updateImageDimensions]);

  /**
   * Handle window resizing
   */
  useEffect(() => {
    function onResize() {
      if (!image || !containerRef.current) return;
      const container = containerRef.current;
      const cW = container.offsetWidth;
      const cH = container.offsetHeight;
      const sX = cW / image.width;
      const sY = cH / image.height;
      const newScale = Math.min(sX, sY, 1);
      setScale(newScale);
      setStageSize({
        width: image.width * newScale,
        height: image.height * newScale,
      });
    }
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [image]);

  /**
   * Sync transformer with the selected shape
   */
  useEffect(() => {
    if (transformerRef.current) {
      if (selectedShapeRef) {
        transformerRef.current.nodes([selectedShapeRef]);
      } else {
        transformerRef.current.nodes([]);
      }
      transformerRef.current.getLayer().batchDraw();
    }
  }, [selectedShapeRef]);

  /**
   * Delete key handling for bounding boxes
   */
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Delete' && selectedObjectIndex !== null && currentResults) {
        removeBboxFromResults(selectedObjectIndex);
        setSelectedObjectIndex(null);
        setSelectedShapeRef(null);
      } else if (e.key === 'Escape') {
        // Cancel current operation
        setSelectedObjectIndex(null);
        setSelectedShapeRef(null);
        setDrawing(false);
        setCurrentBox(null);
        handleClassMenuClose(); // Close class menu if open
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedObjectIndex, removeBboxFromResults, currentResults]);

  // Set appropriate edit mode when detection mode changes
  useEffect(() => {
    if (detectionMode === DETECTION_MODES.IMAGE_PROMPT) {
      setEditMode(EDIT_MODES.DRAW);
    } else {
      setEditMode(EDIT_MODES.SELECT);
    }
  }, [detectionMode]);
  
  // Ensure canvas switches to editing mode when detection results are received
  useEffect(() => {
    if (currentResults) {
      setEditMode(EDIT_MODES.SELECT);
      console.log('Detection results received, switching to SELECT mode:', currentResults);
    }
  }, [currentResults]);

  // Clear selection if the selected object becomes hidden
  useEffect(() => {
    if (selectedObjectIndex !== null && hiddenObjects.includes(selectedObjectIndex)) {
      setSelectedObjectIndex(null);
      setSelectedShapeRef(null);
    }
  }, [hiddenObjects, selectedObjectIndex]);

  /**
   * Mouse down -> possibly start drawing a box if user clicks on empty canvas
   */
  function handleMouseDown(e) {
    // We clicked on the stage itself (not a shape)
    if (e.target === e.target.getStage()) {
      setSelectedObjectIndex(null);
      setSelectedShapeRef(null);
      handleClassMenuClose(); // Close class menu on stage click

      // Pan mode - start dragging the stage
      if (editMode === EDIT_MODES.PAN) {
        setIsDragging(true);
        return;
      }

      // Draw mode - start drawing a box
      if (editMode === EDIT_MODES.DRAW) {
        const pointerPos = e.target.getStage().getPointerPosition();
        // Ensure pointer position is valid
        if (!pointerPos) return;
        const x = (pointerPos.x - stagePosition.x) / scale;
        const y = (pointerPos.y - stagePosition.y) / scale;
        setDrawing(true);
        setStartPoint({ x, y });
        setCurrentBox({ x, y, width: 0, height: 0 });
      }
    }
  }

  /**
   * Mouse move -> update the currently drawn box or pan the stage
   */
  function handleMouseMove(e) {
    const stage = e.target.getStage();
    
    // Pan mode - drag the stage
    if (isDragging && editMode === EDIT_MODES.PAN) {
      const dx = e.evt.movementX;
      const dy = e.evt.movementY;
      setStagePosition({
        x: stagePosition.x + dx,
        y: stagePosition.y + dy
      });
      return;
    }

    // Draw mode - update the box
    if (drawing && editMode === EDIT_MODES.DRAW && startPoint) {
      const pointerPos = stage.getPointerPosition();
      // Ensure pointer position is valid
      if (!pointerPos) return;
      const x = (pointerPos.x - stagePosition.x) / scale;
      const y = (pointerPos.y - stagePosition.y) / scale;
      setCurrentBox({
        x: Math.min(x, startPoint.x),
        y: Math.min(y, startPoint.y),
        width: Math.abs(x - startPoint.x),
        height: Math.abs(y - startPoint.y),
      });
    }
  }

  /**
   * Mouse up -> finalize the box if large enough or stop panning
   */
  function handleMouseUp() {
    // Stop panning
    if (isDragging && editMode === EDIT_MODES.PAN) {
      setIsDragging(false);
      return;
    }

    // Finalize box drawing
    if (drawing && currentBox && image && editMode === EDIT_MODES.DRAW) {
      // Minimum size
      if (currentBox.width > 5 && currentBox.height > 5) {
        // Add the new bounding box to either imagePrompts or detectionResults
        if (detectionMode === DETECTION_MODES.IMAGE_PROMPT) {
          const newBboxes = [...(imagePrompts?.bboxes || [])];
          const newCls = [...(imagePrompts?.cls || [])];
          newBboxes.push([
            currentBox.x / image.width,
            currentBox.y / image.height,
            (currentBox.x + currentBox.width) / image.width,
            (currentBox.y + currentBox.height) / image.height,
          ]);
          newCls.push(0);
          updateImagePrompts(newBboxes, newCls);
        } else if (currentResults) {
          const nbbox = [
            currentBox.x / image.width,
            currentBox.y / image.height,
            (currentBox.x + currentBox.width) / image.width,
            (currentBox.y + currentBox.height) / image.height,
          ];
          // Default to first class if available, otherwise 0
          const defaultClassId = currentResults.classes && currentResults.classes.length > 0 ? 0 : 0;
          addBboxToResults(nbbox, defaultClassId);
        }
      }
      setDrawing(false);
      setCurrentBox(null);
    }
  }

  /**
   * Hover highlighting
   */
  function handleObjectHover(index, entering) {
    setHoveredObject(entering ? index : null);
  }

  /**
   * Select an object by index. Sets up transform handles.
   */
  function handleBoxSelect(e, index, shapeRef) {
    if (editMode !== EDIT_MODES.SELECT) return;
    
    e.cancelBubble = true;
    setSelectedObjectIndex(index);
    setSelectedShapeRef(shapeRef);
  }

  /**
   * After the user drags the bounding box's group, shift box & mask
   */
  function handleGroupDragEnd(e, index) {
    if (!image || !currentResults || !currentResults.objects) return;
    
    const obj = currentResults.objects[index];
    if (!obj || !obj.bbox) return;
    
    const dx = e.target.x();
    const dy = e.target.y();
    const { nbbox, nmask } = shiftBboxAndMask(obj, dx, dy, image.width, image.height);
    updateBboxInResults(index, nbbox, nmask);
    
    // reset group offset
    e.target.x(0);
    e.target.y(0);
  }

  /**
   * After the user resizes the bounding box, apply scale to box & mask
   */
  function handleTransformEnd(e, index) {
    if (!image || !currentResults || !currentResults.objects) return;
    
    const obj = currentResults.objects[index];
    if (!obj || !obj.bbox) return;

    const node = e.target;
    const scaleX = node.scaleX();
    const scaleY = node.scaleY();
    node.scaleX(1);
    node.scaleY(1);

    const { nbbox, nmask } = scaleBboxAndMask(
      obj,
      scaleX,
      scaleY,
      node.x(),
      node.y(),
      image.width,
      image.height
    );
    updateBboxInResults(index, nbbox, nmask);
  }

  /**
   * Delete the selected bounding box
   */
  function handleDeleteSelected() {
    if (selectedObjectIndex !== null && currentResults) {
      removeBboxFromResults(selectedObjectIndex);
      setSelectedObjectIndex(null);
      setSelectedShapeRef(null);
    }
  }

  /**
   * Reset view (pan and zoom)
   */
  function handleResetView() {
    setStagePosition({ x: 0, y: 0 });
    
    if (!image || !containerRef.current) return;
    const container = containerRef.current;
    const cW = container.offsetWidth;
    const cH = container.offsetHeight;
    const sX = cW / image.width;
    const sY = cH / image.height;
    const newScale = Math.min(sX, sY, 1);
    setScale(newScale);
  }

  /**
   * Handle class change
   */
  function handleClassMenuOpen(event) {
    setClassMenuAnchor(event.currentTarget);
  }

  function handleClassMenuClose() {
    setClassMenuAnchor(null);
  }

  function handleClassChange(newClassId) {
    if (selectedObjectIndex !== null && currentResults) {
      updateObjectClass(selectedObjectIndex, newClassId);
      handleClassMenuClose();
    }
  }

  /**
   * Renders bounding boxes and masks from detection results
   */
  function renderDetections() {
    if (!currentResults || !currentResults.classes || !image) {
      return null;
    }
    
    const detectionColors = generateColors(currentResults.classes.length);
    
    console.log("Rendering detections:", currentResults);
    
    if (!Array.isArray(currentResults.objects) || currentResults.objects.length === 0) {
      console.log("No objects to render");
      return null;
    }

    return currentResults.objects.map((obj, i) => {
      // Basic validation for object structure
      if (!obj || obj.class_id === undefined || !obj.bbox || !Array.isArray(obj.bbox)) {
        console.log(`Invalid object at index ${i}:`, obj);
        return null;
      }
      
      // Skip hidden objects
      if (hiddenObjects.includes(i)) return null;
      
      const classIndex = obj.class_id;
      // Ensure classIndex is valid
      if (classIndex < 0 || classIndex >= currentResults.classes.length) {
        console.warn(`Invalid class index ${classIndex} for object ${i}`);
        return null; // Skip rendering invalid objects
      }
      const className = currentResults.classes[classIndex] || 'Unknown';
      const color = detectionColors[classIndex] || theme.palette.primary.main;
      const isHighlighted = hoveredObject === i;
      const isSelected = selectedObjectIndex === i;
      const strokeW = isSelected ? 3 : isHighlighted ? 2.5 : 2;
      const absBox = denormalizeBbox(obj.bbox, image.width, image.height);

      // Local mask points, offset by bounding box
      let localMaskPoints = null;
      if (obj.mask && Array.isArray(obj.mask)) {
        localMaskPoints = getLocalMaskPoints(obj.mask, absBox.x, absBox.y);
      }

      return (
        <Group
          key={i}
          x={absBox.x}
          y={absBox.y}
          draggable={editMode === EDIT_MODES.SELECT}
          onMouseEnter={() => handleObjectHover(i, true)}
          onMouseLeave={() => handleObjectHover(i, false)}
          onClick={(e) => handleBoxSelect(e, i, e.target)}
          onTap={(e) => handleBoxSelect(e, i, e.target)}
          onDragEnd={(e) => handleGroupDragEnd(e, i)}
          ref={isSelected ? (node) => setSelectedShapeRef(node) : null}
        >
          {/* Bounding box */}
          <Rect
            x={0}
            y={0}
            width={absBox.width}
            height={absBox.height}
            stroke={color}
            fill={isSelected || isHighlighted ? color : 'transparent'}
            opacity={isSelected ? 0.2 : isHighlighted ? 0.1 : 1}
            strokeWidth={strokeW}
            dash={isHighlighted && !isSelected ? [10, 5] : undefined}
            lineJoin="round"
            cornerRadius={2}
            onTransformEnd={(e) => handleTransformEnd(e, i)}
            shadowColor={isSelected || isHighlighted ? color : 'transparent'}
            shadowBlur={isSelected ? 8 : isHighlighted ? 4 : 0}
            shadowOpacity={0.3}
          />
          
          {/* Class label with confidence */}
          <Label x={0} y={-28}>
            <Tag 
              fill={color} 
              cornerRadius={4} 
              opacity={0.9}
              shadowColor="rgba(0,0,0,0.3)"
              shadowBlur={3}
              shadowOffsetY={1}
              shadowOpacity={0.3}
            />
            <Text
              text={`${className} ${Math.round((obj.confidence || 0) * 100)}%`}
              fontSize={12}
              fontStyle="bold"
              padding={6}
              fill="white"
            />
          </Label>
          
          {/* Segmentation mask */}
          {localMaskPoints && (
            <Line
              points={localMaskPoints}
              stroke={color}
              strokeWidth={2}
              closed
              fill={color}
              opacity={isSelected ? 0.35 : isHighlighted ? 0.25 : 0.2}  // Increased opacity for better visibility
              shadowColor={isSelected || isHighlighted ? color : 'transparent'}
              shadowBlur={isSelected ? 10 : isHighlighted ? 5 : 0}
              shadowOpacity={0.3}
            />
          )}
        </Group>
      );
    });
  }

  /**
   * Renders boxes from image prompts (for "image-prompt" mode)
   */
  function renderDrawingBoxes() {
    if (detectionMode !== DETECTION_MODES.IMAGE_PROMPT || !image || !imagePrompts || !Array.isArray(imagePrompts.bboxes)) {
      return null;
    }
    const boxes = imagePrompts.bboxes.map((bbox, i) => {
      if (!Array.isArray(bbox) || bbox.length !== 4) return null; // Add validation
      const x = bbox[0] * image.width;
      const y = bbox[1] * image.height;
      const w = (bbox[2] - bbox[0]) * image.width;
      const h = (bbox[3] - bbox[1]) * image.height;
      return (
        <Rect
          key={i}
          x={x}
          y={y}
          width={w}
          height={h}
          stroke={theme.palette.secondary.main}
          strokeWidth={2}
          dash={[10, 5]}
          fill={theme.palette.secondary.main}
          opacity={0.1}
        />
      );
    });
    // Currently drawing box
    const newBox = currentBox && (
      <Rect
        x={currentBox.x}
        y={currentBox.y}
        width={currentBox.width}
        height={currentBox.height}
        stroke={theme.palette.primary.main}
        strokeWidth={2}
        dash={[10, 5]}
        fill={theme.palette.primary.main}
        opacity={0.15}
      />
    );
    return (
      <Group>
        {boxes}
        {newBox}
      </Group>
    );
  }

  /**
   * Display instructions
   */
  function getInstructions() {
    if (editMode === EDIT_MODES.SELECT && selectedObjectIndex !== null) {
      return 'Edit Mode: Drag box to move, resize handles to adjust, press Delete key to remove.';
    }
    if (editMode === EDIT_MODES.DRAW) {
      return 'Draw Mode: Click and drag to create a new bounding box.';
    }
    if (editMode === EDIT_MODES.PAN) {
      return 'Pan Mode: Click and drag to move the canvas view.';
    }
    if (detectionMode === DETECTION_MODES.IMAGE_PROMPT) {
      return 'Draw boxes on the image to use as prompts for detection.';
    }
    if (currentResults) {
      return 'Select Mode: Click on boxes to select and edit them.';
    }
    return '';
  }

  return (
    <Paper
      elevation={3}
      sx={{
        height: '100%',
        width: '100%',
        overflow: 'hidden',
        position: 'relative',
        bgcolor: theme.palette.grey[100],
        borderRadius: 2,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      ref={containerRef}
    >
      {currentImage ? (
        <>
          {/* Mode controls */}
          <Box
            sx={{
              position: 'absolute',
              top: 10,
              left: 10,
              zIndex: 10,
              display: 'flex',
              gap: 1,
              bgcolor: 'rgba(255,255,255,0.9)',
              borderRadius: 1,
              p: 0.5,
              boxShadow: '0px 2px 4px rgba(0,0,0,0.1)',
            }}
          >
            <Tooltip title="Select Mode">
              <IconButton 
                size="small" 
                color={editMode === EDIT_MODES.SELECT ? "primary" : "default"}
                onClick={() => setEditMode(EDIT_MODES.SELECT)}
                sx={{ 
                  bgcolor: editMode === EDIT_MODES.SELECT ? 'rgba(238, 76, 44, 0.1)' : 'transparent',
                  '&:hover': { bgcolor: editMode === EDIT_MODES.SELECT ? 'rgba(238, 76, 44, 0.15)' : 'rgba(0, 0, 0, 0.04)' }
                }}
              >
                <EditIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Draw Mode">
              <IconButton 
                size="small" 
                color={editMode === EDIT_MODES.DRAW ? "primary" : "default"}
                onClick={() => setEditMode(EDIT_MODES.DRAW)}
                sx={{ 
                  bgcolor: editMode === EDIT_MODES.DRAW ? 'rgba(238, 76, 44, 0.1)' : 'transparent',
                  '&:hover': { bgcolor: editMode === EDIT_MODES.DRAW ? 'rgba(238, 76, 44, 0.15)' : 'rgba(0, 0, 0, 0.04)' }
                }}
              >
                <BrushIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Pan Mode">
              <IconButton 
                size="small" 
                color={editMode === EDIT_MODES.PAN ? "primary" : "default"}
                onClick={() => setEditMode(EDIT_MODES.PAN)}
                sx={{ 
                  bgcolor: editMode === EDIT_MODES.PAN ? 'rgba(238, 76, 44, 0.1)' : 'transparent',
                  '&:hover': { bgcolor: editMode === EDIT_MODES.PAN ? 'rgba(238, 76, 44, 0.15)' : 'rgba(0, 0, 0, 0.04)' }
                }}
              >
                <PanToolIcon />
              </IconButton>
            </Tooltip>
            
            {selectedObjectIndex !== null && (
              <>
                <Tooltip title="Change Class">
                  <IconButton 
                    size="small" 
                    color="primary"
                    onClick={handleClassMenuOpen}
                    sx={{ 
                      bgcolor: 'rgba(238, 76, 44, 0.1)',
                      '&:hover': { bgcolor: 'rgba(238, 76, 44, 0.15)' }
                    }}
                  >
                    <ClassIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete Selected">
                  <IconButton 
                    size="small" 
                    color="error"
                    onClick={handleDeleteSelected}
                    sx={{ 
                      bgcolor: 'rgba(244, 67, 54, 0.1)',
                      '&:hover': { bgcolor: 'rgba(244, 67, 54, 0.15)' }
                    }}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
              </>
            )}
          </Box>
          
          {/* Class Tags Display - Similar to DinoX UI */}
          {currentResults && Array.isArray(currentResults.classes) && currentResults.classes.length > 0 && (
            <Box
              sx={{
                position: 'absolute',
                top: 10,
                left: '50%',
                transform: 'translateX(-50%)',
                zIndex: 10,
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                gap: 0.5,
                maxWidth: '80%',
                bgcolor: 'rgba(255,255,255,0.9)',
                borderRadius: 2,
                py: 0.5,
                px: 1,
                boxShadow: '0px 2px 4px rgba(0,0,0,0.1)',
              }}
            >
              {currentResults.classes.map((className, index) => {
                const colors = generateColors(currentResults.classes.length);
                const color = colors[index];
                const objectCount = currentResults.objects.filter(obj => obj && obj.class_id === index).length;
                
                return (
                  <Chip
                    key={index}
                    label={`${className} (${objectCount})`}
                    size="small"
                    sx={{
                      bgcolor: color,
                      color: 'white',
                      fontWeight: 500,
                      fontSize: '0.75rem',
                      height: 24,
                      '& .MuiChip-label': { px: 1 },
                      boxShadow: '0px 1px 2px rgba(0,0,0,0.2)',
                    }}
                  />
                );
              })}
            </Box>
          )}
          
          {/* Class selection menu */}
          {currentResults && Array.isArray(currentResults.classes) && Array.isArray(currentResults.objects) && (
            <Menu
              anchorEl={classMenuAnchor}
              open={classMenuOpen}
              onClose={handleClassMenuClose}
              sx={{ 
                '& .MuiPaper-root': { 
                  boxShadow: 3,
                  borderRadius: 1,
                  mt: 1
                }
              }}
            >
              {currentResults.classes.map((className, index) => {
                const colors = generateColors(currentResults.classes.length);
                // Ensure object exists before accessing class_id
                const selectedObject = selectedObjectIndex !== null ? currentResults.objects[selectedObjectIndex] : null;
                const isSelected = selectedObject && selectedObject.class_id === index;

                return (
                  <MenuItem
                    key={index}
                    onClick={() => handleClassChange(index)}
                    selected={isSelected}
                    sx={{
                      '&.Mui-selected': {
                        backgroundColor: 'rgba(238, 76, 44, 0.08)',
                        '&:hover': {
                          backgroundColor: 'rgba(238, 76, 44, 0.12)',
                        },
                      },
                    }}
                  >
                    <ListItemIcon>
                      <Box
                        sx={{
                          width: 16,
                          height: 16,
                          borderRadius: '50%',
                          bgcolor: colors[index],
                        }}
                      />
                    </ListItemIcon>
                    <ListItemText>{className}</ListItemText>
                  </MenuItem>
                );
              })}
            </Menu>
          )}
          
          {/* Instructions */}
          {getInstructions() && (
            <Box
              sx={{
                position: 'absolute',
                top: 60,
                left: '50%',
                transform: 'translateX(-50%)',
                bgcolor: 'rgba(0,0,0,0.7)',
                color: 'white',
                py: 0.5,
                px: 2,
                borderRadius: 2,
                zIndex: 10,
                boxShadow: '0px 2px 4px rgba(0,0,0,0.2)',
              }}
            >
              <Typography variant="caption" sx={{ fontWeight: 500 }}>{getInstructions()}</Typography>
            </Box>
          )}
          
          {/* Canvas */}
          {imageStatus === 'loaded' ? (
            <Stage
              width={stageSize.width}
              height={stageSize.height}
              scale={{ x: scale, y: scale }}
              position={stagePosition}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              ref={stageRef}
            >
              <Layer ref={layerRef}>
                <KonvaImage image={image} />
                {renderDetections()}
                {renderDrawingBoxes()}
                {selectedShapeRef && editMode === EDIT_MODES.SELECT && (
                  <Transformer
                    ref={transformerRef}
                    rotateEnabled={false}
                    keepRatio={false}
                    borderDash={[5, 5]}
                    borderStroke={theme.palette.primary.main}
                    anchorStroke={theme.palette.primary.main}
                    anchorFill={theme.palette.common.white}
                    anchorSize={10}
                    enabledAnchors={['top-left', 'top-right', 'bottom-left', 'bottom-right']}
                    boundBoxFunc={(oldBox, newBox) => {
                      // Limit resize dimensions to prevent collapsing
                      if (newBox.width < 5 || newBox.height < 5) {
                        return oldBox;
                      }
                      return newBox;
                    }}
                  />
                )}
              </Layer>
            </Stage>
          ) : (
            <Skeleton variant="rectangular" width="80%" height="80%" animation="wave" />
          )}
          
          {/* Reset view button */}
          <Box
            sx={{
              position: 'absolute',
              bottom: 10,
              right: 10,
              zIndex: 10,
            }}
          >
            <Tooltip title="Reset View">
              <IconButton
                size="small"
                onClick={handleResetView}
                sx={{ 
                  bgcolor: 'rgba(255,255,255,0.9)',
                  boxShadow: '0px 2px 4px rgba(0,0,0,0.1)',
                  '&:hover': { bgcolor: 'rgba(255,255,255,1)' }
                }}
              >
                <CenterFocusStrongIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </>
      ) : (
        <Box sx={{ p: 3, textAlign: 'center', maxWidth: 400 }}>
          <Typography variant="h6" color="textSecondary">
            No Image Selected
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
            Upload an image to get started with object detection
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default AnnotationCanvas;
