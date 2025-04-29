import React from 'react';
import { 
  Box, 
  List, 
  ListItem, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText, 
  Paper, 
  Divider,
  Typography,
  useTheme 
} from '@mui/material';
import TextFormatIcon from '@mui/icons-material/TextFormat';
import ImageIcon from '@mui/icons-material/Image';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import { useApp, DETECTION_MODES } from '../context/AppContext';

const Sidebar = () => {
  const theme = useTheme();
  const { detectionMode, setDetectionMode, currentImage } = useApp();
  
  const handleModeChange = (mode) => {
    setDetectionMode(mode);
  };
  
  const modeItems = [
    {
      id: DETECTION_MODES.TEXT_PROMPT,
      name: 'Text Prompt',
      icon: <TextFormatIcon />,
      description: 'Detect objects using text prompt'
    },
    {
      id: DETECTION_MODES.IMAGE_PROMPT,
      name: 'Image Prompt',
      icon: <ImageIcon />,
      description: 'Draw and detect objects'
    },
    {
      id: DETECTION_MODES.PROMPT_FREE,
      name: 'Prompt Free',
      icon: <AutoFixHighIcon />,
      description: 'Automatic detection'
    }
  ];
  
  return (
    <Paper
      elevation={2}
      sx={{
        height: '100%',
        width: '100%',
        backgroundColor: 'background.paper',
        borderRadius: 2,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
        <Typography variant="h6" fontWeight="bold">
          YOLOe Detection
        </Typography>
      </Box>

      <Divider />
      
      <Box sx={{ p: 2 }}>
        <Typography variant="subtitle2" color="textSecondary" sx={{ mb: 1 }}>
          Detection Mode
        </Typography>
        
        <List sx={{ p: 0 }}>
          {modeItems.map((item) => (
            <ListItem key={item.id} disablePadding sx={{ mb: 1 }}>
              <ListItemButton
                selected={detectionMode === item.id}
                onClick={() => handleModeChange(item.id)}
                sx={{
                  borderRadius: 1,
                  transition: 'all 0.2s',
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(238, 76, 44, 0.08)',
                    '&:hover': {
                      backgroundColor: 'rgba(238, 76, 44, 0.12)',
                    },
                  },
                }}
                disabled={!currentImage}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 40,
                    color: detectionMode === item.id ? 'primary.main' : 'neutral.500',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.name} 
                  secondary={item.description}
                  primaryTypographyProps={{ 
                    variant: 'body2',
                    fontWeight: detectionMode === item.id ? 600 : 400,
                    color: detectionMode === item.id ? 'primary.main' : 'textPrimary'
                  }}
                  secondaryTypographyProps={{ 
                    variant: 'caption',
                    sx: { 
                      color: detectionMode === item.id ? 'primary.main' : 'textSecondary',
                      opacity: 0.7
                    }
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>
      
      <Box sx={{ flexGrow: 1 }} />
      
      <Box sx={{ p: 2 }}>
        <Typography variant="caption" color="textSecondary">
          EurekAnno - YOLOe Detection
        </Typography>
      </Box>
    </Paper>
  );
};

export default Sidebar; 