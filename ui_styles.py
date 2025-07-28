#!/usr/bin/env python3

# Star Wars Opening Crawl CSS
opening_crawl_css = """
/* Star Wars Opening Crawl Effect */
.opening-crawl-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: #000;
    color: #feda4a;
    font-family: 'Franklin Gothic Medium', 'Arial Narrow', Arial, sans-serif;
    overflow: hidden;
    z-index: 10000;
    opacity: 1;
    transition: opacity 0.5s ease-out;
}

.opening-crawl-container.hidden {
    display: none !important;
}

.star-field {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: #000;
}

.star {
    position: absolute;
    background: white;
    border-radius: 50%;
    opacity: 0.8;
    animation: twinkle 3s infinite;
}

@keyframes twinkle {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 1; }
}

.crawl-content {
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    width: 60%;
    text-align: center;
    font-size: 24px;
    line-height: 1.8;
    animation: crawl 12s linear forwards;
}

@keyframes crawl {
    0% {
        top: 100%;
        transform: translateX(-50%) rotateX(20deg);
    }
    100% {
        top: -100%;
        transform: translateX(-50%) rotateX(60deg);
    }
}

.episode-title {
    font-size: 48px;
    font-weight: bold;
    color: #4fc3f7;
    margin-bottom: 40px;
    text-shadow: 0 0 10px #4fc3f7;
}

.story-text {
    font-size: 20px;
    line-height: 1.6;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
}

.skip-button {
    position: absolute;
    bottom: 30px;
    right: 30px;
    background: rgba(79,195,247,0.2);
    border: 2px solid #4fc3f7;
    color: #4fc3f7;
    padding: 12px 24px;
    border-radius: 8px;
    cursor: pointer;
    font-family: 'Orbitron', monospace;
    font-size: 16px;
    font-weight: bold;
    transition: all 0.3s ease;
    box-shadow: 0 0 10px rgba(79,195,247,0.3);
    animation: pulse-button 2s infinite;
}

.skip-button:hover {
    background: rgba(79,195,247,0.4);
    box-shadow: 0 0 20px #4fc3f7;
    transform: scale(1.05);
}

@keyframes pulse-button {
    0%, 100% { box-shadow: 0 0 10px rgba(79,195,247,0.3); }
    50% { box-shadow: 0 0 20px rgba(79,195,247,0.6); }
}

.EVIL-CORP-logo {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 72px;
    font-weight: bold;
    color: #4fc3f7;
    text-shadow: 0 0 20px #4fc3f7;
    opacity: 0;
    animation: logo-fade 4s ease-in-out;
}

@keyframes logo-fade {
    0% { opacity: 0; transform: translate(-50%, -50%) scale(0.5); }
    20% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
    80% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
    100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
}

@media (max-width: 768px) {
    .crawl-content {
        width: 80%;
        font-size: 18px;
    }
    
    .episode-title {
        font-size: 32px;
    }
    
    .story-text {
        font-size: 16px;
    }
}
"""

# Star Wars themed CSS (main interface)
star_wars_css = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600&display=swap');

/* Main container styling */
.gradio-container {
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
    color: #00ff41;
    font-family: 'Orbitron', monospace;
    min-height: 100vh;
}

/* Header styling */
.header {
    background: linear-gradient(90deg, #001122 0%, #003366 50%, #001122 100%);
    border: 2px solid #00ffff;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    text-align: center;
    box-shadow: 0 0 20px #00ffff, inset 0 0 20px rgba(0,255,255,0.1);
    animation: glow-border 3s ease-in-out infinite alternate;
}

@keyframes glow-border {
    from { box-shadow: 0 0 20px #00ffff, inset 0 0 20px rgba(0,255,255,0.1); }
    to { box-shadow: 0 0 30px #00ffff, inset 0 0 30px rgba(0,255,255,0.2); }
}

.header h1 {
    color: #00ffff;
    font-size: 2.5em;
    font-weight: 900;
    text-shadow: 0 0 10px #00ffff;
    margin: 0;
    letter-spacing: 3px;
}

.header h2 {
    color: #00ff41;
    font-size: 1.2em;
    font-weight: 400;
    margin: 10px 0 0 0;
    text-shadow: 0 0 5px #00ff41;
}

/* Chat interface styling */
.chat-container {
    background: rgba(0,20,40,0.9);
    border: 1px solid #00ff41;
    border-radius: 15px;
    padding: 15px;
    margin: 10px 0;
    box-shadow: 0 0 15px rgba(0,255,65,0.3);
    backdrop-filter: blur(5px);
}

/* Message styling */
.message {
    margin: 10px 0;
    padding: 15px;
    border-radius: 10px;
    font-family: 'Exo 2', sans-serif;
}

.user-message {
    background: linear-gradient(135deg, #002040 0%, #003060 100%);
    border-left: 4px solid #00ffff;
    color: #ffffff;
    text-align: right;
    margin-left: 20%;
}

.assistant-message {
    background: linear-gradient(135deg, #001a00 0%, #003300 100%);
    border-left: 4px solid #00ff41;
    color: #00ff41;
    margin-right: 20%;
}

.system-message {
    background: linear-gradient(135deg, #200020 0%, #400040 100%);
    border: 1px solid #ff00ff;
    color: #ff88ff;
    text-align: center;
    font-style: italic;
}

/* Input styling */
.input-container {
    background: rgba(0,30,60,0.8);
    border: 2px solid #00ff41;
    border-radius: 10px;
    padding: 10px;
    margin: 10px 0;
    box-shadow: 0 0 10px rgba(0,255,65,0.5);
}

input[type="text"] {
    background: rgba(0,0,0,0.7) !important;
    border: 1px solid #00ff41 !important;
    color: #00ff41 !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 14px !important;
    padding: 12px !important;
    border-radius: 5px !important;
    box-shadow: inset 0 0 10px rgba(0,255,65,0.2) !important;
}

input[type="text"]:focus {
    border-color: #00ffff !important;
    box-shadow: 0 0 15px rgba(0,255,255,0.5) !important;
    outline: none !important;
}

/* Dropdown styling */
.dropdown select {
    background: rgba(0,0,0,0.7) !important;
    border: 1px solid #00ff41 !important;
    color: #00ff41 !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 14px !important;
    padding: 12px !important;
    border-radius: 5px !important;
    box-shadow: inset 0 0 10px rgba(0,255,65,0.2) !important;
}

.dropdown select:focus {
    border-color: #00ffff !important;
    box-shadow: 0 0 15px rgba(0,255,255,0.5) !important;
    outline: none !important;
}

.dropdown option {
    background: rgba(0,20,40,0.9) !important;
    color: #00ff41 !important;
    padding: 8px !important;
}

/* Label styling for dropdown */
label {
    color: #00ffff !important;
    font-family: 'Orbitron', monospace !important;
    font-weight: 600 !important;
    text-shadow: 0 0 5px #00ffff !important;
}

/* Button styling */
button {
    background: linear-gradient(135deg, #003366 0%, #006699 100%) !important;
    border: 2px solid #00ffff !important;
    color: #ffffff !important;
    font-family: 'Orbitron', monospace !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}

button:hover {
    background: linear-gradient(135deg, #006699 0%, #0099cc 100%) !important;
    box-shadow: 0 0 20px rgba(0,255,255,0.6) !important;
    transform: translateY(-2px) !important;
}

/* Status indicators */
.status-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse 2s infinite;
}

.status-online {
    background: #00ff41;
    box-shadow: 0 0 10px #00ff41;
}

.status-processing {
    background: #ffff00;
    box-shadow: 0 0 10px #ffff00;
}

.status-error {
    background: #ff0000;
    box-shadow: 0 0 10px #ff0000;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

/* Tool result styling */
.tool-result {
    background: rgba(0,50,100,0.3);
    border: 1px solid #0088ff;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    font-family: 'Exo 2', monospace;
    color: #88ccff;
}

.tool-result-success {
    border-color: #00ff41;
    background: rgba(0,50,0,0.3);
}

.tool-result-error {
    border-color: #ff4444;
    background: rgba(50,0,0,0.3);
    color: #ff8888;
}

/* Sidebar styling */
.sidebar {
    background: linear-gradient(180deg, #001122 0%, #002244 100%);
    border: 1px solid #00ffff;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
    box-shadow: 0 0 15px rgba(0,255,255,0.2);
}

.sidebar h3 {
    color: #00ffff;
    text-shadow: 0 0 5px #00ffff;
    border-bottom: 1px solid #00ffff;
    padding-bottom: 5px;
    margin-bottom: 15px;
}

.tool-list {
    list-style: none;
    padding: 0;
}

.tool-item {
    background: rgba(0,40,80,0.5);
    border: 1px solid #0066cc;
    border-radius: 5px;
    padding: 8px 12px;
    margin: 5px 0;
    color: #88ccff;
    font-size: 12px;
    transition: all 0.3s ease;
}

.tool-item:hover {
    background: rgba(0,60,120,0.7);
    border-color: #00aaff;
    color: #ffffff;
    cursor: pointer;
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 12px;
}

::-webkit-scrollbar-track {
    background: #001122;
    border-radius: 6px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #00ffff 0%, #0088cc 100%);
    border-radius: 6px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, #00ccff 0%, #0066aa 100%);
}

/* Responsive design */
@media (max-width: 768px) {
    .header h1 {
        font-size: 2em;
    }
    
    .user-message {
        margin-left: 5%;
    }
    
    .assistant-message {
        margin-right: 5%;
    }
}

/* Loading animation */
.loading {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid rgba(0,255,255,0.3);
    border-radius: 50%;
    border-top-color: #00ffff;
    animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Holographic effect */
.holographic {
    position: relative;
    overflow: hidden;
}

.holographic::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(45deg, transparent, rgba(0,255,255,0.1), transparent);
    animation: hologram 3s linear infinite;
    pointer-events: none;
}

@keyframes hologram {
    0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
    100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
}
"""

def get_combined_css():
    """Return combined CSS for the SRYODA interface"""
    return opening_crawl_css + star_wars_css 