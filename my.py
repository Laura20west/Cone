from kivy.app import App
from kivy.uix.webview import WebView
from kivy.core.window import Window

class StreamlitApp(App):
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)  # White background
        webview = WebView(url='https://laura20west-fcone-main-lelf8u.streamlit.app/', enable_javascript=True)
        return webview

if __name__ == '__main__':
    StreamlitApp().run()
