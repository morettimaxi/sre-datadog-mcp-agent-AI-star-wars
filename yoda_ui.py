#!/usr/bin/env python3

import gradio as gr
from dotenv import load_dotenv

# Import our modular YODA components
from ui_styles import get_combined_css
from ui_components import (
    create_simple_intro, create_header, create_sidebar, 
    create_examples_sidebar, create_footer, get_common_commands, 
    get_initial_messages
)
from ui_handlers import (
    process_yoda_message, on_dropdown_change, 
    execute_command, clear_history
)

# Initialize
load_dotenv()


def create_yoda_ui():
    """Create the main YODA UI with modular components"""
    
    with gr.Blocks(
        css=get_combined_css(), 
        title="YODA - Master SRE of the Galaxy",
        head="""
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="theme-color" content="#00ffff">
        <meta name="description" content="Strategic SRE Operations & DataDog Analytics - Star Wars themed monitoring interface">
        """
    ) as interface:
        # Intro animation
        gr.HTML(create_simple_intro())
        
        # Header
        gr.HTML(create_header())
        
        # Main layout
        with gr.Row():
            # Main chat area
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    [],
                    elem_id="chatbot",
                    height=500,
                    show_label=False,
                    container=True,
                    elem_classes=["chat-container"],
                    type="tuples"
                )
                
                # Command input section
                common_commands = get_common_commands()
                
                with gr.Row():
                    with gr.Column(scale=4):
                        command_dropdown = gr.Dropdown(
                            choices=[""] + common_commands,
                            value="",
                            label="🎯 Quick Commands",
                            info="Select a common command or type your own below",
                            elem_classes=["input-container"]
                        )
                        msg = gr.Textbox(
                            show_label=False,
                            placeholder="Enter your SRE command, young Padawan... or select from dropdown above",
                            container=True,
                            elem_classes=["input-container"]
                        )
                    send_btn = gr.Button("🚀 Execute", scale=1, variant="primary")
                
                with gr.Row():
                    clear_btn = gr.Button("🗑️ Clear Console", variant="secondary")
                    status = gr.HTML("<span class='status-indicator status-online'></span> Systems Online")
            
            # Sidebar
            with gr.Column(scale=1):
                gr.HTML(create_sidebar())
                gr.HTML(create_examples_sidebar())
        
        # Footer
        gr.HTML(create_footer())
        
        # Wire up events
        command_dropdown.change(on_dropdown_change, [command_dropdown, msg], [msg])
        msg.submit(execute_command, [command_dropdown, msg, chatbot], [chatbot, command_dropdown, msg])
        send_btn.click(execute_command, [command_dropdown, msg, chatbot], [chatbot, command_dropdown, msg])
        clear_btn.click(clear_history, outputs=[chatbot, command_dropdown, msg])
        
        # Load initial messages
        interface.load(lambda: get_initial_messages(), outputs=[chatbot])
    
    return interface



if __name__ == "__main__":
    # Create and launch the interface
    ui = create_yoda_ui()
    
    print("🚀 Launching YODA Galactic Command Center...")
    print("🌟 May the Force be with your Infrastructure!")
    
    ui.launch(
        server_name="0.0.0.0",
        server_port=None,  # Let Gradio find an available port
        share=False,
        show_error=True,
        debug=True,
        quiet=False
    ) 