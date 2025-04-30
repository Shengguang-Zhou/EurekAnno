import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider,
  Tabs,
  Tab,
  Stack,
  Badge,
  IconButton,
  Tooltip,
  useTheme
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import { useApp } from '../context/AppContext';

const generateColors = (count) => {
  const colors = [];
  for (let i = 0; i < count; i++) {
    const hue = (i * 137.5) % 360;
    colors.push(`hsl(${hue}, 70%, 60%)`);
  }
  return colors;
};

const ResultsPanel = () => {
  const theme = useTheme();
  const { 
    currentResults,
    hiddenObjects,
    toggleObjectVisibility
  } = useApp();
  
  const [activeTab, setActiveTab] = useState(0);
  const [selectedClass, setSelectedClass] = useState(null);
  
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    setSelectedClass(null);
  };
  
  const handleClassSelect = (classId) => {
    setSelectedClass(selectedClass === classId ? null : classId);
  };
  
  if (!currentResults || !currentResults.classes || !currentResults.objects) {
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
          No detection results yet
        </Typography>
        <Typography variant="body2" color="textSecondary" textAlign="center" sx={{ mt: 1 }}>
          Select a detection mode and click "Detect Objects"
        </Typography>
      </Paper>
    );
  }
  
  const { classes, objects } = currentResults;
  const classColors = generateColors(classes?.length || 0);
  
  // Group objects by class
  const objectsByClass = {};
  objects.forEach((obj) => {
    if (!obj || obj.class_id === undefined) return;
    
    const classId = obj.class_id;
    if (!objectsByClass[classId]) {
      objectsByClass[classId] = [];
    }
    objectsByClass[classId].push(obj);
  });
  
  return (
    <Paper
      elevation={2}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 2,
        overflow: 'hidden'
      }}
    >
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="fullWidth"
          textColor="primary"
          indicatorColor="primary"
          sx={{ minHeight: 36 }}
        >
          <Tab label="Classes" sx={{ minHeight: 36, py: 0.5 }} />
          <Tab label="Objects" sx={{ minHeight: 36, py: 0.5 }} />
        </Tabs>
      </Box>
      
      <Box
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          p: 1.5,
          maxHeight: 'calc(100% - 48px)',
          borderRadius: 1,
          bgcolor: 'background.paper',
          boxShadow: 'inset 0 0 5px rgba(0,0,0,0.05)'
        }}
      >
        {activeTab === 0 ? (
          <ClassesTab 
            classes={classes || []} 
            objectsByClass={objectsByClass} 
            classColors={classColors}
            selectedClass={selectedClass}
            onClassSelect={handleClassSelect}
          />
        ) : (
          <ObjectsTab 
            objects={objects || []} 
            classes={classes || []} 
            selectedClass={selectedClass}
            classColors={classColors}
            hiddenObjects={hiddenObjects}
            onToggleVisibility={toggleObjectVisibility}
          />
        )}
      </Box>
    </Paper>
  );
};

const ClassesTab = ({ classes, objectsByClass, classColors, selectedClass, onClassSelect }) => {
  if (!classes || !classes.length) {
    return (
      <Box sx={{ py: 1, textAlign: 'center' }}>
        <Typography variant="body2" color="textSecondary" fontSize="0.75rem">
          No classes detected
        </Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={1} sx={{ height: '100%' }}>
      <Typography variant="subtitle2" fontSize="0.8rem">
        Detected Classes ({classes.length})
      </Typography>
      
      <List disablePadding dense sx={{ 
        maxHeight: 'calc(100% - 24px)', 
        overflow: 'auto', 
        borderRadius: 1,
        bgcolor: 'grey.50',
        '& .MuiListItem-root': {
          borderRadius: 1,
          mb: 0.5,
          mx: 0.5,
          width: 'calc(100% - 8px)'
        }
      }}>
        {classes.map((className, index) => {
          const objectCount = objectsByClass[index]?.length || 0;
          const isSelected = selectedClass === index;
          
          return (
            <React.Fragment key={index}>
              <ListItem 
                button 
                selected={isSelected}
                onClick={() => onClassSelect(index)}
                sx={{
                  borderRadius: 1,
                  py: 0.5,
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(238, 76, 44, 0.08)',
                    '&:hover': {
                      backgroundColor: 'rgba(238, 76, 44, 0.12)',
                    },
                  },
                }}
              >
                <Box
                  sx={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    bgcolor: classColors[index] || '#999',
                    mr: 1.5,
                    flexShrink: 0
                  }}
                />
                <ListItemText 
                  primary={className || 'Unknown'} 
                  primaryTypographyProps={{
                    fontWeight: isSelected ? 600 : 400,
                    variant: 'body2',
                    fontSize: '0.75rem'
                  }}
                />
                <Chip 
                  size="small" 
                  label={objectCount} 
                  sx={{ 
                    height: 16,
                    fontSize: '0.65rem',
                    bgcolor: isSelected ? 'primary.main' : 'grey.200',
                    color: isSelected ? 'primary.contrastText' : 'text.secondary'
                  }} 
                />
              </ListItem>
              
              {index < classes.length - 1 && <Divider variant="fullWidth" component="li" />}
            </React.Fragment>
          );
        })}
      </List>
    </Stack>
  );
};

const ObjectsTab = ({ objects, classes, selectedClass, classColors, hiddenObjects, onToggleVisibility }) => {
  const filteredObjects = selectedClass !== null && objects
    ? objects.filter(obj => obj && obj.class_id === selectedClass)
    : objects || [];
    
  if (!filteredObjects.length) {
    return (
      <Box sx={{ py: 1, textAlign: 'center' }}>
        <Typography variant="body2" color="textSecondary" fontSize="0.75rem">
          No objects found matching the selected criteria
        </Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={1} sx={{ height: '100%' }}>
      <Typography variant="subtitle2" fontSize="0.8rem">
        {selectedClass !== null 
          ? `Objects of class "${classes[selectedClass] || 'Unknown'}" (${filteredObjects.length})`
          : `All Objects (${filteredObjects.length})`
        }
      </Typography>
      
      <List disablePadding dense sx={{ 
        maxHeight: 'calc(100% - 24px)', 
        overflow: 'auto',
        borderRadius: 1,
        bgcolor: 'grey.50',
        '& .MuiListItem-root': {
          borderRadius: 1,
          mb: 0.5,
          mx: 0.5,
          width: 'calc(100% - 8px)'
        } 
      }}>
        {filteredObjects.map((obj, index) => {
          if (!obj || obj.class_id === undefined) return null;
          
          const objectIndex = objects.indexOf(obj);
          const className = classes[obj.class_id] || 'Unknown';
          const color = classColors[obj.class_id] || '#999';
          const isHidden = hiddenObjects.includes(objectIndex);
          
          return (
            <React.Fragment key={index}>
              <ListItem sx={{ py: 0.5 }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                    <Box
                      sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: color,
                        mr: 1,
                        flexShrink: 0
                      }}
                    />
                    <Typography variant="body2" fontSize="0.75rem" fontWeight={500}>
                      {className}
                    </Typography>
                    <Box sx={{ flexGrow: 1 }} />
                    <Tooltip title={isHidden ? "Show object" : "Hide object"}>
                      <IconButton 
                        size="small" 
                        onClick={() => onToggleVisibility(objectIndex)}
                        sx={{ p: 0.5, mr: 0.5 }}
                      >
                        {isHidden 
                          ? <VisibilityOffIcon sx={{ fontSize: 14 }} color="action" /> 
                          : <VisibilityIcon sx={{ fontSize: 14 }} color="primary" />
                        }
                      </IconButton>
                    </Tooltip>
                    <Chip 
                      size="small" 
                      label={`${Math.round((obj.confidence || 0) * 100)}%`}
                      sx={{ 
                        height: 16,
                        fontSize: '0.65rem',
                        bgcolor: 'grey.200',
                        opacity: isHidden ? 0.5 : 1
                      }} 
                    />
                  </Box>
                  
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, pl: 2 }}>
                    <Chip 
                      size="small" 
                      label={`ID: ${objectIndex}`}
                      variant="outlined"
                      sx={{ 
                        height: 16,
                        fontSize: '0.65rem',
                        opacity: isHidden ? 0.5 : 1
                      }} 
                    />
                    {obj.bbox && (
                      <Chip 
                        size="small" 
                        label="Has Bbox"
                        variant="outlined"
                        sx={{ 
                          height: 16,
                          fontSize: '0.65rem',
                          opacity: isHidden ? 0.5 : 1
                        }} 
                      />
                    )}
                    {obj.mask && (
                      <Chip 
                        size="small" 
                        label="Has Mask"
                        variant="outlined"
                        sx={{ 
                          height: 16,
                          fontSize: '0.65rem',
                          opacity: isHidden ? 0.5 : 1
                        }} 
                      />
                    )}
                  </Box>
                </Box>
              </ListItem>
              
              {index < filteredObjects.length - 1 && <Divider variant="fullWidth" component="li" />}
            </React.Fragment>
          );
        })}
      </List>
    </Stack>
  );
};

export default ResultsPanel;
