import gradio as gr
from ui_service.tabs.court_tab import render_court_tab
from ui_service.tabs.inference_tab import render_inference_tab

with gr.Blocks(title="Basketball Analysis") as demo:
    gr.Markdown("# Basketball Analysis")
    
    with gr.Tabs():
        render_court_tab()
        render_inference_tab()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)