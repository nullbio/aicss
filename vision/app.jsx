import React, { useState, useRef, useEffect } from 'react';
import { X, Move, ChevronLeft, ChevronRight, Type, Square, Palette } from 'lucide-react';

const VisualCssCompiler = () => {
    const [splitPosition, setSplitPosition] = useState(50);
    const [elements, setElements] = useState([]);
    const [selectedElement, setSelectedElement] = useState(null);
    const [activeMode, setActiveMode] = useState('box'); // 'box', 'text', 'select'
    const [showColorPicker, setShowColorPicker] = useState(false);
    const [colorPickerPosition, setColorPickerPosition] = useState({ x: 0, y: 0 });
    const [generatedCode, setGeneratedCode] = useState('');
    const [naturalLanguage, setNaturalLanguage] = useState('');
    const canvasRef = useRef(null);
    const dragRef = useRef(null);
    const [isDraggingSplitter, setIsDraggingSplitter] = useState(false);

    // Sample login form example
    useEffect(() => {
        // Add example elements after component mounts
        const exampleElements = [
            {
                id: 1,
                type: 'box',
                x: 200,
                y: 150,
                width: 300,
                height: 200,
                color: '#333333',
                zIndex: 1
            },
            {
                id: 2,
                type: 'text',
                x: 320,
                y: 170,
                content: 'Log In Form',
                fontSize: 18,
                color: '#ffffff',
                zIndex: 2
            },
            {
                id: 3,
                type: 'box',
                x: 460,
                y: 160,
                width: 30,
                height: 30,
                color: '#666666',
                zIndex: 3
            },
            {
                id: 4,
                type: 'text',
                x: 470,
                y: 175,
                content: 'X',
                fontSize: 16,
                color: '#ffffff',
                zIndex: 4
            }
        ];

        setElements(exampleElements);
        updateOutput(exampleElements);
    }, []);

    // Update the natural language and HTML/CSS output when elements change
    const updateOutput = (updatedElements) => {
        // Generate natural language description
        let nlDescription = '';

        updatedElements.forEach(el => {
            if (el.type === 'box') {
                nlDescription += `Create a ${el.color} box at position (${el.x}, ${el.y}) with width ${el.width}px and height ${el.height}px.\n`;

                // Detect if this might be a close button
                const possibleCloseText = updatedElements.find(textEl =>
                    textEl.type === 'text' &&
                    textEl.content.trim() === 'X' &&
                    textEl.x >= el.x &&
                    textEl.x <= el.x + el.width &&
                    textEl.y >= el.y &&
                    textEl.y <= el.y + el.height
                );

                if (possibleCloseText) {
                    nlDescription += `This appears to be a close button.\n`;
                }
            } else if (el.type === 'text') {
                nlDescription += `Add text "${el.content}" at position (${el.x}, ${el.y}) with font size ${el.fontSize}px in color ${el.color}.\n`;
            }
        });

        // Check for login form pattern
        const blackBox = updatedElements.find(el => el.type === 'box' && el.color === '#333333');
        const loginText = updatedElements.find(el => el.type === 'text' && el.content.includes('Log In'));

        if (blackBox && loginText) {
            nlDescription += `\nThis appears to be a login form container.\n`;
        }

        setNaturalLanguage(nlDescription);

        // Generate HTML/CSS code based on the elements
        let html = `<!DOCTYPE html>\n<html>\n<head>\n  <style>\n`;

        // CSS
        updatedElements.forEach(el => {
            if (el.type === 'box') {
                const isCloseButton = updatedElements.find(textEl =>
                    textEl.type === 'text' &&
                    textEl.content.trim() === 'X' &&
                    textEl.x >= el.x &&
                    textEl.x <= el.x + el.width &&
                    textEl.y >= el.y &&
                    textEl.y <= el.y + el.height
                );

                if (isCloseButton) {
                    html += `    .close-button {\n`;
                    html += `      position: absolute;\n`;
                    html += `      top: ${el.y}px;\n`;
                    html += `      left: ${el.x}px;\n`;
                    html += `      width: ${el.width}px;\n`;
                    html += `      height: ${el.height}px;\n`;
                    html += `      background-color: ${el.color};\n`;
                    html += `      display: flex;\n`;
                    html += `      justify-content: center;\n`;
                    html += `      align-items: center;\n`;
                    html += `      color: white;\n`;
                    html += `      cursor: pointer;\n`;
                    html += `    }\n\n`;
                } else if (loginText && el === blackBox) {
                    html += `    .login-container {\n`;
                    html += `      position: absolute;\n`;
                    html += `      top: ${el.y}px;\n`;
                    html += `      left: ${el.x}px;\n`;
                    html += `      width: ${el.width}px;\n`;
                    html += `      height: ${el.height}px;\n`;
                    html += `      background-color: ${el.color};\n`;
                    html += `      border-radius: 5px;\n`;
                    html += `    }\n\n`;
                } else {
                    html += `    #box-${el.id} {\n`;
                    html += `      position: absolute;\n`;
                    html += `      top: ${el.y}px;\n`;
                    html += `      left: ${el.x}px;\n`;
                    html += `      width: ${el.width}px;\n`;
                    html += `      height: ${el.height}px;\n`;
                    html += `      background-color: ${el.color};\n`;
                    html += `    }\n\n`;
                }
            } else if (el.type === 'text') {
                if (el.content.trim() === 'X') {
                    // Skip X text since it's handled by the close button
                } else if (el.content.includes('Log In')) {
                    html += `    .login-title {\n`;
                    html += `      position: absolute;\n`;
                    html += `      top: ${el.y}px;\n`;
                    html += `      left: ${el.x}px;\n`;
                    html += `      font-size: ${el.fontSize}px;\n`;
                    html += `      color: ${el.color};\n`;
                    html += `      font-weight: bold;\n`;
                    html += `    }\n\n`;
                } else {
                    html += `    #text-${el.id} {\n`;
                    html += `      position: absolute;\n`;
                    html += `      top: ${el.y}px;\n`;
                    html += `      left: ${el.x}px;\n`;
                    html += `      font-size: ${el.fontSize}px;\n`;
                    html += `      color: ${el.color};\n`;
                    html += `    }\n\n`;
                }
            }
        });

        html += `  </style>\n</head>\n<body>\n`;

        // HTML
        const closeButton = updatedElements.find(el => el.type === 'box' && updatedElements.find(textEl =>
            textEl.type === 'text' &&
            textEl.content.trim() === 'X' &&
            textEl.x >= el.x &&
            textEl.x <= el.x + el.width &&
            textEl.y >= el.y &&
            textEl.y <= el.y + el.height
        ));

        if (blackBox && loginText) {
            html += `  <div class="login-container">\n`;
            html += `    <div class="login-title">Log In Form</div>\n`;

            if (closeButton) {
                html += `    <div class="close-button">X</div>\n`;
            }

            html += `    <!-- Login form fields would go here -->\n`;
            html += `  </div>\n`;
        } else {
            // Generic elements
            updatedElements.forEach(el => {
                if (el.type === 'box' && el !== closeButton && el !== blackBox) {
                    html += `  <div id="box-${el.id}"></div>\n`;
                } else if (el.type === 'text' && el.content.trim() !== 'X' && !el.content.includes('Log In')) {
                    html += `  <div id="text-${el.id}">${el.content}</div>\n`;
                }
            });

            if (closeButton) {
                html += `  <div class="close-button">X</div>\n`;
            }
        }

        html += `</body>\n</html>`;

        setGeneratedCode(html);
    };

    // Add a new element to the canvas
    const addElement = (type, e) => {
        if (!canvasRef.current) return;

        const rect = canvasRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const newElement = {
            id: Date.now(),
            type,
            x,
            y,
            zIndex: elements.length + 1
        };

        if (type === 'box') {
            newElement.width = 100;
            newElement.height = 100;
            newElement.color = '#333333';
        } else if (type === 'text') {
            newElement.content = 'New Text';
            newElement.fontSize = 16;
            newElement.color = '#000000';
        }

        const updatedElements = [...elements, newElement];
        setElements(updatedElements);
        setSelectedElement(newElement);
        updateOutput(updatedElements);
    };

    // Handle mouse events for dragging elements
    const handleMouseDown = (e, element) => {
        if (activeMode !== 'select') return;

        e.stopPropagation();
        setSelectedElement(element);

        const startX = e.clientX;
        const startY = e.clientY;
        const startElementX = element.x;
        const startElementY = element.y;

        const handleMouseMove = (moveEvent) => {
            const deltaX = moveEvent.clientX - startX;
            const deltaY = moveEvent.clientY - startY;

            const updatedElements = elements.map(el => {
                if (el.id === element.id) {
                    return {
                        ...el,
                        x: startElementX + deltaX,
                        y: startElementY + deltaY
                    };
                }
                return el;
            });

            setElements(updatedElements);
            updateOutput(updatedElements);
        };

        const handleMouseUp = () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    };

    // Handle resizing an element
    const handleResize = (e, corner) => {
        if (!selectedElement || selectedElement.type !== 'box') return;

        e.stopPropagation();

        const startX = e.clientX;
        const startY = e.clientY;
        const startWidth = selectedElement.width;
        const startHeight = selectedElement.height;
        const startElementX = selectedElement.x;
        const startElementY = selectedElement.y;

        const handleMouseMove = (moveEvent) => {
            const deltaX = moveEvent.clientX - startX;
            const deltaY = moveEvent.clientY - startY;

            const updatedElements = elements.map(el => {
                if (el.id === selectedElement.id) {
                    let newX = el.x;
                    let newY = el.y;
                    let newWidth = el.width;
                    let newHeight = el.height;

                    if (corner === 'se') {
                        newWidth = Math.max(20, startWidth + deltaX);
                        newHeight = Math.max(20, startHeight + deltaY);
                    } else if (corner === 'sw') {
                        newX = startElementX + deltaX;
                        newWidth = Math.max(20, startWidth - deltaX);
                        newHeight = Math.max(20, startHeight + deltaY);
                    } else if (corner === 'ne') {
                        newY = startElementY + deltaY;
                        newWidth = Math.max(20, startWidth + deltaX);
                        newHeight = Math.max(20, startHeight - deltaY);
                    } else if (corner === 'nw') {
                        newX = startElementX + deltaX;
                        newY = startElementY + deltaY;
                        newWidth = Math.max(20, startWidth - deltaX);
                        newHeight = Math.max(20, startHeight - deltaY);
                    }

                    return {
                        ...el,
                        x: newX,
                        y: newY,
                        width: newWidth,
                        height: newHeight
                    };
                }
                return el;
            });

            setElements(updatedElements);
            updateOutput(updatedElements);
        };

        const handleMouseUp = () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    };

    // Handle editing text content
    const handleTextEdit = (content) => {
        if (!selectedElement || selectedElement.type !== 'text') return;

        const updatedElements = elements.map(el => {
            if (el.id === selectedElement.id) {
                return {
                    ...el,
                    content
                };
            }
            return el;
        });

        setElements(updatedElements);
        setSelectedElement({ ...selectedElement, content });
        updateOutput(updatedElements);
    };

    // Handle changing element color
    const handleColorChange = (color) => {
        if (!selectedElement) return;

        const updatedElements = elements.map(el => {
            if (el.id === selectedElement.id) {
                return {
                    ...el,
                    color
                };
            }
            return el;
        });

        setElements(updatedElements);
        setSelectedElement({ ...selectedElement, color });
        updateOutput(updatedElements);
    };

    // Show color picker for the selected element
    const openColorPicker = (e) => {
        e.stopPropagation();
        setColorPickerPosition({ x: e.clientX, y: e.clientY });
        setShowColorPicker(true);
    };

    // Handle splitter drag to resize the panels
    const handleSplitterMouseDown = (e) => {
        e.preventDefault();
        setIsDraggingSplitter(true);

        const handleMouseMove = (moveEvent) => {
            const containerWidth = document.body.clientWidth;
            const percentage = (moveEvent.clientX / containerWidth) * 100;
            setSplitPosition(Math.min(Math.max(20, percentage), 80));
        };

        const handleMouseUp = () => {
            setIsDraggingSplitter(false);
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    };

    // Handle canvas click to add new elements
    const handleCanvasClick = (e) => {
        if (activeMode === 'box' || activeMode === 'text') {
            addElement(activeMode, e);
        } else {
            setSelectedElement(null);
        }
    };

    return (
        <div className="flex flex-col h-screen bg-gray-100">
            {/* Toolbar */}
            <div className="bg-gray-800 text-white p-2 flex items-center">
                <h1 className="text-xl font-bold mr-4">Visual CSS Compiler</h1>
                <div className="flex space-x-2">
                    <button
                        className={`p-2 rounded ${activeMode === 'select' ? 'bg-blue-600' : 'bg-gray-700'}`}
                        onClick={() => setActiveMode('select')}
                    >
                        <Move size={16} />
                    </button>
                    <button
                        className={`p-2 rounded ${activeMode === 'box' ? 'bg-blue-600' : 'bg-gray-700'}`}
                        onClick={() => setActiveMode('box')}
                    >
                        <Square size={16} />
                    </button>
                    <button
                        className={`p-2 rounded ${activeMode === 'text' ? 'bg-blue-600' : 'bg-gray-700'}`}
                        onClick={() => setActiveMode('text')}
                    >
                        <Type size={16} />
                    </button>
                    {selectedElement && (
                        <button
                            className="p-2 rounded bg-gray-700"
                            onClick={openColorPicker}
                        >
                            <Palette size={16} />
                        </button>
                    )}
                </div>
                <div className="ml-auto text-sm">
                    Mode: {activeMode === 'select' ? 'Move & Edit' : activeMode === 'box' ? 'Add Box' : 'Add Text'}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex flex-1 overflow-hidden">
                {/* Left Panel - Visual Editor */}
                <div
                    className="bg-white relative overflow-hidden"
                    style={{ width: `${splitPosition}%` }}
                >
                    <div
                        ref={canvasRef}
                        className="w-full h-full relative"
                        onClick={handleCanvasClick}
                    >
                        {elements.map(element => (
                            <div
                                key={element.id}
                                className={`absolute ${selectedElement?.id === element.id ? 'ring-2 ring-blue-500' : ''}`}
                                style={{
                                    left: `${element.x}px`,
                                    top: `${element.y}px`,
                                    zIndex: element.zIndex,
                                    cursor: activeMode === 'select' ? 'move' : 'default'
                                }}
                                onClick={(e) => activeMode === 'select' && handleMouseDown(e, element)}
                            >
                                {element.type === 'box' && (
                                    <div
                                        style={{
                                            width: `${element.width}px`,
                                            height: `${element.height}px`,
                                            backgroundColor: element.color
                                        }}
                                    >
                                        {selectedElement?.id === element.id && (
                                            <>
                                                <div
                                                    className="absolute top-0 left-0 w-2 h-2 bg-white border border-blue-500 cursor-nw-resize"
                                                    onMouseDown={(e) => handleResize(e, 'nw')}
                                                />
                                                <div
                                                    className="absolute top-0 right-0 w-2 h-2 bg-white border border-blue-500 cursor-ne-resize"
                                                    onMouseDown={(e) => handleResize(e, 'ne')}
                                                />
                                                <div
                                                    className="absolute bottom-0 left-0 w-2 h-2 bg-white border border-blue-500 cursor-sw-resize"
                                                    onMouseDown={(e) => handleResize(e, 'sw')}
                                                />
                                                <div
                                                    className="absolute bottom-0 right-0 w-2 h-2 bg-white border border-blue-500 cursor-se-resize"
                                                    onMouseDown={(e) => handleResize(e, 'se')}
                                                />
                                            </>
                                        )}
                                    </div>
                                )}
                                {element.type === 'text' && (
                                    <div
                                        style={{
                                            fontSize: `${element.fontSize}px`,
                                            color: element.color
                                        }}
                                    >
                                        {selectedElement?.id === element.id ? (
                                            <input
                                                type="text"
                                                value={element.content}
                                                onChange={(e) => handleTextEdit(e.target.value)}
                                                onClick={(e) => e.stopPropagation()}
                                                className="border border-blue-500 bg-transparent outline-none p-1"
                                                style={{
                                                    fontSize: `${element.fontSize}px`,
                                                    color: element.color,
                                                    width: `${Math.max(100, element.content.length * element.fontSize * 0.6)}px`
                                                }}
                                            />
                                        ) : (
                                            element.content
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Splitter */}
                <div
                    className={`w-1 bg-gray-300 hover:bg-blue-500 cursor-col-resize ${isDraggingSplitter ? 'bg-blue-500' : ''}`}
                    onMouseDown={handleSplitterMouseDown}
                />

                {/* Right Panel - Code Output */}
                <div
                    className="flex flex-col bg-gray-100 overflow-hidden"
                    style={{ width: `${100 - splitPosition}%` }}
                >
                    <div className="p-2 border-b border-gray-300 flex">
                        <button className="px-3 py-1 bg-white border border-gray-300 mr-2">Natural Language</button>
                        <button className="px-3 py-1 bg-gray-100 border border-gray-300">HTML/CSS</button>
                    </div>
                    <div className="flex-1 overflow-auto flex">
                        <div className="w-1/2 p-4 bg-white overflow-auto">
                            <h3 className="text-lg font-semibold mb-2">Natural Language</h3>
                            <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-3 rounded">
                                {naturalLanguage}
                            </pre>
                        </div>
                        <div className="w-1/2 p-4 overflow-auto">
                            <h3 className="text-lg font-semibold mb-2">Generated HTML/CSS</h3>
                            <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-3 rounded">
                                {generatedCode}
                            </pre>
                        </div>
                    </div>
                </div>
            </div>

            {/* Color Picker Tooltip */}
            {showColorPicker && selectedElement && (
                <div
                    className="fixed bg-white shadow-lg rounded p-3 z-50"
                    style={{
                        left: colorPickerPosition.x,
                        top: colorPickerPosition.y,
                    }}
                >
                    <div className="flex flex-col space-y-2">
                        <div className="text-sm font-semibold">Select Color</div>
                        <div className="flex h-6 w-48 bg-gradient-to-r from-black via-red-500 via-yellow-500 via-green-500 via-blue-500 to-purple-500">
                            <input
                                type="range"
                                min="0"
                                max="360"
                                className="w-full opacity-0 cursor-pointer"
                                onChange={(e) => {
                                    const hue = e.target.value;
                                    handleColorChange(`hsl(${hue}, 70%, 50%)`);
                                }}
                            />
                        </div>
                        <div className="flex justify-between">
                            <button
                                className="px-2 py-1 bg-gray-200 text-xs rounded"
                                onClick={() => setShowColorPicker(false)}
                            >
                                Close
                            </button>
                            <div
                                className="w-6 h-6 border border-gray-300"
                                style={{ backgroundColor: selectedElement.color }}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default VisualCssCompiler;
