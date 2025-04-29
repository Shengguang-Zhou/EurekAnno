import React from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  ImageList, 
  ImageListItem, 
  Stack,
  useTheme
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useApp } from '../context/AppContext';

const ImageGallery = () => {
  const theme = useTheme();
  const { 
    images, 
    currentImageIndex, 
    goToImage, 
    detectionResults 
  } = useApp();
  
  // Always show 8 images per row
  const COLUMNS = 8;
  
  if (images.length === 0) {
    return (
      <Paper
        elevation={2}
        sx={{
          p: 2,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          borderRadius: 2
        }}
      >
        <Typography variant="body1" color="textSecondary" textAlign="center">
          No images uploaded yet
        </Typography>
        <Typography variant="body2" color="textSecondary" textAlign="center" sx={{ mt: 1 }}>
          Upload images to start detection
        </Typography>
      </Paper>
    );
  }
  
  return (
    <Paper
      elevation={2}
      sx={{
        p: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 2,
        overflow: 'hidden'
      }}
    >
      <Stack spacing={1} height="100%">
        <Typography variant="subtitle1">
          Image Gallery ({images.length})
        </Typography>
        
        <Box sx={{ 
          overflow: 'auto', 
          flexGrow: 1,
          '&::-webkit-scrollbar': {
            width: '6px',
            height: '6px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(0, 0, 0, 0.2)',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: 'rgba(0, 0, 0, 0.05)',
          }
        }}>
          <ImageList 
            cols={COLUMNS} 
            gap={4}
            sx={{ 
              m: 0,
              // Support showing 8 rows of images without scrolling (in a perfect case scenario)
              // This still allows scrolling when there are more than 64 images
              gridTemplateRows: `repeat(8, 1fr)`,
            }}
          >
            {images.map((image, index) => {
              const isSelected = index === currentImageIndex;
              const hasResults = !!detectionResults[image.id];
              
              return (
                <ImageListItem 
                  key={image.id} 
                  onClick={() => goToImage(index)}
                  sx={{
                    cursor: 'pointer',
                    borderRadius: 1,
                    overflow: 'hidden',
                    position: 'relative',
                    border: isSelected ? `2px solid ${theme.palette.primary.main}` : 'none',
                    transform: isSelected ? 'scale(0.95)' : 'scale(1)',
                    transition: 'all 0.2s ease-in-out',
                    height: '100% !important', // Override MUI default
                    '&:hover': {
                      transform: 'scale(0.95)',
                      '& .image-overlay': {
                        opacity: 1
                      }
                    }
                  }}
                >
                  <img
                    src={image.url}
                    alt={image.name}
                    loading="lazy"
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      aspectRatio: '1/1'
                    }}
                  />
                  
                  {/* Overlay with name - show on hover or selected */}
                  <Box
                    className="image-overlay"
                    sx={{
                      position: 'absolute',
                      bottom: 0,
                      left: 0,
                      right: 0,
                      bgcolor: 'rgba(0, 0, 0, 0.6)',
                      p: 0.5,
                      opacity: isSelected ? 1 : 0,
                      transition: 'opacity 0.2s ease-in-out'
                    }}
                  >
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        color: 'white',
                        display: 'block',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        fontSize: '0.65rem'
                      }}
                    >
                      {image.name}
                    </Typography>
                  </Box>
                  
                  {/* Detection status */}
                  {hasResults && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 2,
                        right: 2,
                        borderRadius: '50%',
                        bgcolor: 'background.paper',
                        width: 14,
                        height: 14,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      <CheckCircleIcon 
                        sx={{ fontSize: 14 }}
                        color="success" 
                      />
                    </Box>
                  )}
                </ImageListItem>
              );
            })}
          </ImageList>
        </Box>
      </Stack>
    </Paper>
  );
};

export default ImageGallery; 