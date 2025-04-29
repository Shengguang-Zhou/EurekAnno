import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  Divider, 
  Paper, 
  Stack, 
  Typography, 
  Alert,
  Snackbar,
  IconButton,
  useTheme
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import { useApp } from '../context/AppContext';
import yoloeApi from '../api/yoloeApi';

const DetectionControls = () => {
  const theme = useTheme();
  const { 
    currentImage, 
    removeImage,
    prevImage,
    nextImage,
    images,
    currentImageIndex,
    detectionResults,
    isLoading,
    setIsLoading,
    currentResults
  } = useApp();
  
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');
  
  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };
  
  const showSnackbar = (message, severity = 'success') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };
  
  const handleExport = async () => {
    if (!currentImage) return;
    
    const result = detectionResults[currentImage.id];
    if (!result) {
      showSnackbar('No detection results to export', 'warning');
      return;
    }
    
    try {
      setIsLoading(true);
      
      // Prepare data for export
      const exportData = {
        filename_base: currentImage.name.split('.')[0],
        image_width: currentImage.width,
        image_height: currentImage.height,
        class_name_to_id: result.classes.reduce((acc, name, idx) => ({...acc, [name]: idx}), {}),
        annotations: result.objects.map(obj => ({
          class_name: result.classes[obj.class_id],
          bbox: obj.bbox
        }))
      };
      
      // Call export API
      const blob = await yoloeApi.exportYolo(exportData);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${currentImage.name.split('.')[0]}.txt`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      showSnackbar('YOLO format exported successfully');
    } catch (error) {
      console.error('Export error:', error);
      showSnackbar(`Error: ${error.message || 'Failed to export annotations'}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleExportAll = async () => {
    const resultsToExport = Object.keys(detectionResults);
    
    if (resultsToExport.length === 0) {
      showSnackbar('No detection results to export', 'warning');
      return;
    }
    
    try {
      setIsLoading(true);
      
      // Prepare data for batch export
      const imagesData = {};
      resultsToExport.forEach(imageId => {
        const image = images.find(img => img.id === imageId);
        const result = detectionResults[imageId];
        
        imagesData[image.name] = {
          image_width: image.width,
          image_height: image.height,
          annotations: result.objects.map(obj => ({
            class_name: result.classes[obj.class_id],
            bbox: obj.bbox
          }))
        };
      });
      
      const exportData = {
        zip_filename_base: 'yolo_annotations',
        class_name_to_id: Object.values(detectionResults)[0].classes.reduce(
          (acc, name, idx) => ({...acc, [name]: idx}), {}
        ),
        images_data: imagesData
      };
      
      // Call batch export API
      const blob = await yoloeApi.exportYoloBatch(exportData);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'yolo_annotations.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      showSnackbar('All annotations exported successfully');
    } catch (error) {
      console.error('Batch export error:', error);
      showSnackbar(`Error: ${error.message || 'Failed to export annotations'}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleDeleteImage = () => {
    if (!currentImage) return;
    
    // Confirm before deleting
    if (window.confirm(`Are you sure you want to delete "${currentImage.name}"?`)) {
      removeImage(currentImage.id);
      showSnackbar('Image deleted successfully');
    }
  };
  
  const hasResults = currentImage && detectionResults[currentImage.id];
  const canNavigatePrev = currentImageIndex > 0;
  const canNavigateNext = currentImageIndex < images.length - 1;
  
  return (
    <Paper
      elevation={2}
      sx={{
        p: 2,
        borderRadius: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <Typography variant="subtitle1" gutterBottom>
        Navigation & Export
      </Typography>
      
      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" color="textSecondary" gutterBottom>
          {currentImage ? `Current: ${currentImage.name}` : 'No image selected'}
        </Typography>
        
        <Stack direction="row" spacing={1} alignItems="center">
          <IconButton 
            size="small" 
            onClick={prevImage} 
            disabled={!canNavigatePrev}
            sx={{ color: 'primary.main' }}
          >
            <NavigateBeforeIcon />
          </IconButton>
          
          <Typography variant="body2" sx={{ flexGrow: 1, textAlign: 'center' }}>
            {currentImageIndex >= 0 ? `${currentImageIndex + 1} / ${images.length}` : '-'}
          </Typography>
          
          <IconButton 
            size="small" 
            onClick={nextImage} 
            disabled={!canNavigateNext}
            sx={{ color: 'primary.main' }}
          >
            <NavigateNextIcon />
          </IconButton>
        </Stack>
      </Box>
      
      <Divider sx={{ mb: 2 }} />
      
      {currentImage && !currentResults ? (
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center', 
          flexGrow: 1,
          textAlign: 'center'
        }}>
          <Typography variant="body2" color="textSecondary">
            No detection results yet
          </Typography>
          <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5 }}>
            Select a detection mode and click "Detect Objects"
          </Typography>
        </Box>
      ) : (
        <Stack spacing={1} sx={{ mt: 'auto' }}>
          <Button
            variant="outlined"
            color="primary"
            startIcon={<DownloadIcon />}
            onClick={handleExport}
            disabled={!hasResults}
            size="small"
          >
            Export Current (YOLO)
          </Button>
          
          <Button
            variant="outlined"
            color="primary"
            startIcon={<DownloadIcon />}
            onClick={handleExportAll}
            disabled={Object.keys(detectionResults).length === 0}
            size="small"
          >
            Export All (YOLO)
          </Button>
          
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteOutlineIcon />}
            onClick={handleDeleteImage}
            disabled={!currentImage}
            size="small"
          >
            Delete Image
          </Button>
        </Stack>
      )}
      
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={snackbarSeverity} 
          elevation={6}
          variant="filled"
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Paper>
  );
};

export default DetectionControls; 