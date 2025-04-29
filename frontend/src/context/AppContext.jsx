import React, { createContext, useState, useContext, useCallback } from 'react';

// Create context
const AppContext = createContext();

// Mode constants
export const DETECTION_MODES = {
  TEXT_PROMPT: 'text-prompt',
  IMAGE_PROMPT: 'image-prompt',
  PROMPT_FREE: 'prompt-free'
};

// Helper to deep-clone objects (to keep state immutable)
const clone = (v) => JSON.parse(JSON.stringify(v));

// Provider component
export const AppProvider = ({ children }) => {
  // State for uploaded images and their results
  const [images, setImages] = useState([]);
  const [currentImageIndex, setCurrentImageIndex] = useState(-1);
  const [detectionMode, setDetectionMode] = useState(DETECTION_MODES.TEXT_PROMPT);
  const [textPrompts, setTextPrompts] = useState([]);
  const [imagePrompts, setImagePrompts] = useState({ bboxes: [], cls: [] });
  const [detectionResults, setDetectionResults] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hiddenObjects, setHiddenObjects] = useState({});

  // Hovered/selected object indices for synergy between ResultsPanel & Canvas
  // Defaults to -1 meaning "none"
  const [hoveredObjectIndex, setHoveredObjectIndex] = useState(-1);
  const [selectedObjectIndex, setSelectedObjectIndex] = useState(-1);

  // Get current image
  const currentImage =
    currentImageIndex >= 0 && currentImageIndex < images.length
      ? images[currentImageIndex]
      : null;

  // Get current results
  const currentResults = currentImage?.id ? detectionResults[currentImage.id] : null;
  const currentHiddenObjects = currentImage ? (hiddenObjects[currentImage.id] || []) : [];

  // Add new image
  const addImage = useCallback((file) => {
    const id = Date.now().toString();
    const url = URL.createObjectURL(file);
    setImages((prev) => [...prev, { id, file, url, name: file.name, width: 0, height: 0 }]);
    setCurrentImageIndex((idx) => (idx < 0 ? 0 : idx + 1));
    return id;
  }, []);

  // Remove image
  const removeImage = useCallback((id) => {
    setImages((prev) => {
      const nxt = prev.filter((img) => img.id !== id);
      URL.revokeObjectURL(prev.find((i) => i.id === id)?.url || '');
      setCurrentImageIndex((idx) => (idx >= nxt.length ? nxt.length - 1 : idx));
      return nxt;
    });
    setDetectionResults((prev) => {
      const n = { ...prev };
      delete n[id];
      return n;
    });
    setHiddenObjects((prev) => {
      const n = { ...prev };
      delete n[id];
      return n;
    });
  }, []);

  // Add text prompt
  const addTextPrompt = useCallback((p) => setTextPrompts((prev) => [...prev, p]), []);

  // Remove text prompt
  const removeTextPrompt = useCallback((idx) => setTextPrompts((p) => p.filter((_, i) => i !== idx)), []);

  // Clear all text prompts
  const clearTextPrompts = useCallback(() => setTextPrompts([]), []);

  // Update image prompts
  const updateImagePrompts = useCallback((bboxes, cls) => setImagePrompts({ bboxes, cls }), []);

  // Add detection result
  const addDetectionResult = useCallback((imageId, result) => {
    setDetectionResults((prev) => ({ ...prev, [imageId]: clone(result) }));
  }, []);

  // Navigate to specific image
  const goToImage = useCallback((idx) => idx >= 0 && idx < images.length && setCurrentImageIndex(idx), [images.length]);

  // Navigate to next image
  const nextImage = useCallback(() => currentImageIndex < images.length - 1 && setCurrentImageIndex((i) => i + 1), [currentImageIndex, images.length]);

  // Navigate to previous image
  const prevImage = useCallback(() => currentImageIndex > 0 && setCurrentImageIndex((i) => i - 1), [currentImageIndex]);

  // Update image dimensions
  const updateImageDimensions = useCallback((id, w, h) => {
    if (!w || !h) return;
    setImages((prev) => prev.map((img) => (img.id === id ? { ...img, width: w, height: h } : img)));
  }, []);

  // Add a new bbox to the current results
  const addBboxToResults = useCallback((bbox, classId = 0, mask = null) => {
    if (!currentImage) return;
    setDetectionResults((prev) => {
      const res = clone(prev);
      if (!res[currentImage.id]) return prev;
      res[currentImage.id].objects.push({ class_id: classId, bbox, mask, confidence: 1 });
      return res;
    });
  }, [currentImage]);

  // Update an existing bbox (and optional mask) in the current results
  const updateBboxInResults = useCallback((index, updatedBbox, updatedMask = null) => {
    if (!currentImage) return;
    setDetectionResults((prev) => {
      const res = clone(prev);
      const obj = res[currentImage.id]?.objects[index];
      if (!obj) return prev;
      obj.bbox = updatedBbox;
      if (updatedMask) obj.mask = updatedMask;
      return res;
    });
  }, [currentImage]);

  // Remove a bbox from the current results
  const removeBboxFromResults = useCallback((index) => {
    if (!currentImage) return;
    setDetectionResults((prev) => {
      const res = clone(prev);
      if (!res[currentImage.id]) return prev;
      res[currentImage.id].objects.splice(index, 1);
      return res;
    });
    // Also remove from hidden objects if it was hidden
    setHiddenObjects((prev) => {
      const hidden = prev[currentImage.id] || [];
      if (!hidden.includes(index)) return prev;
      
      const newHidden = hidden.filter(i => i !== index).map(i => i > index ? i - 1 : i);
      return {
        ...prev,
        [currentImage.id]: newHidden
      };
    });
  }, [currentImage]);

  // Update the class of an existing object
  const updateObjectClass = useCallback((index, newClassId) => {
    if (!currentImage) return;
    setDetectionResults((prev) => {
      const res = clone(prev);
      const obj = res[currentImage.id]?.objects[index];
      if (!obj) return prev;
      obj.class_id = newClassId;
      return res;
    });
  }, [currentImage]);

  // Toggle object visibility
  const toggleObjectVisibility = useCallback((index) => {
    if (!currentImage) return;
    
    setHiddenObjects((prev) => {
      const hidden = prev[currentImage.id] || [];
      let newHidden;
      
      if (hidden.includes(index)) {
        newHidden = hidden.filter(i => i !== index);
      } else {
        newHidden = [...hidden, index];
      }
      
      return {
        ...prev,
        [currentImage.id]: newHidden
      };
    });
  }, [currentImage]);

  // Context value
  const contextValue = {
    images,
    currentImage,
    currentImageIndex,
    detectionMode,
    textPrompts,
    imagePrompts,
    detectionResults,
    currentResults,
    isLoading,
    error,
    hiddenObjects: currentHiddenObjects,
    hoveredObjectIndex,
    selectedObjectIndex,

    // Methods
    setDetectionMode,
    addImage,
    removeImage,
    addTextPrompt,
    removeTextPrompt,
    clearTextPrompts,
    updateImagePrompts,
    addDetectionResult,
    goToImage,
    nextImage,
    prevImage,
    updateImageDimensions,
    setIsLoading,
    setError,
    addBboxToResults,
    updateBboxInResults,
    removeBboxFromResults,
    updateObjectClass,
    toggleObjectVisibility,

    // Hover/selection methods
    setHoveredObjectIndex,
    setSelectedObjectIndex
  };

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
};

// Custom hook for using the context
export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export default AppContext;
