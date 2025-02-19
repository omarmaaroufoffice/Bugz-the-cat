import streamlit as st
import streamlit.components.v1 as components
import json
from functools import wraps

def make_accessible(func):
    """Decorator to add accessibility features to Streamlit pages."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Add skip link
        components.html(
            """
            <a href="#main-content" class="skip-link">Skip to main content</a>
            """,
            height=0
        )
        
        # Add main landmark
        st.markdown("""
            <main id="main-content" role="main" aria-label="Main content">
                <div role="region" aria-label="Page content">
        """, unsafe_allow_html=True)
        
        # Call the original function
        result = func(*args, **kwargs)
        
        # Close main landmark
        st.markdown("""
                </div>
            </main>
        """, unsafe_allow_html=True)
        
        return result
    
    return wrapper

def custom_menu_button(label="Menu", icon="≡", key=None):
    """
    Create a custom menu button with proper accessibility attributes.
    Uses Streamlit's component system for better integration.
    """
    component_value = components.html(
        f"""
        <div id="menu-wrapper-{key}" style="margin: 1rem 0;">
            <button
                id="menu-button-{key}"
                class="menu-button"
                aria-label="{label}"
                aria-controls="menu-content-{key}"
                aria-haspopup="true"
                role="button"
                style="
                    min-height: 44px;
                    padding: 8px 16px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    font-weight: 600;
                    border-radius: 8px;
                    cursor: pointer;
                    background: linear-gradient(135deg, #2E7D32, #43A047);
                    color: #FFFFFF;
                    border: none;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                "
            >
                <span aria-hidden="true" style="font-size: 1.2rem;">{icon}</span>
                <span style="font-size: 1rem;">{label}</span>
            </button>
        </div>
        <script>
            const button = document.getElementById('menu-button-{key}');
            let isExpanded = false;
            
            button.addEventListener('click', () => {{
                isExpanded = !isExpanded;
                button.setAttribute('aria-expanded', isExpanded);
                window.parent.postMessage({{
                    type: 'streamlit:message',
                    action: 'menuButtonClicked',
                    value: isExpanded,
                    key: '{key}'
                }}, '*');
            }});
            
            // Handle keyboard navigation
            button.addEventListener('keydown', (e) => {{
                if (e.key === 'Enter' || e.key === ' ') {{
                    e.preventDefault();
                    button.click();
                }}
            }});
        </script>
        """,
        height=60,
        key=f"menu_button_{key}"
    )
    
    return component_value

def custom_scrollable_region(content, max_height="300px", label=None, key=None):
    """
    Create a custom scrollable region with proper keyboard navigation and ARIA attributes.
    Uses Streamlit's component system for better integration.
    """
    if isinstance(content, (dict, list)):
        content = json.dumps(content, indent=2)
    
    component_value = components.html(
        f"""
        <div
            id="scrollable-{key}"
            class="scrollable-region"
            role="region"
            aria-label="{label or 'Scrollable content'}"
            tabindex="0"
            style="
                max-height: {max_height};
                overflow-y: auto;
                padding: 1rem;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: #FFFFFF;
                margin: 1rem 0;
            "
        >
            <div class="content">
                {content}
            </div>
        </div>
        
        <style>
            .scrollable-region:focus {{
                outline: 2px solid #2E7D32;
                outline-offset: 2px;
            }}
            
            .scrollable-region:focus-visible {{
                box-shadow: 0 0 0 4px rgba(46, 125, 50, 0.2);
            }}
            
            .content {{
                line-height: 1.5;
                color: #1A1A1A;
            }}
            
            .content pre {{
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
        </style>
        
        <script>
            const region = document.getElementById('scrollable-{key}');
            
            region.addEventListener('keydown', (e) => {{
                const scrollAmount = 40;
                const pageScrollAmount = region.clientHeight;
                
                switch (e.key) {{
                    case 'ArrowDown':
                        e.preventDefault();
                        region.scrollTop += scrollAmount;
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        region.scrollTop -= scrollAmount;
                        break;
                    case 'PageDown':
                        e.preventDefault();
                        region.scrollTop += pageScrollAmount;
                        break;
                    case 'PageUp':
                        e.preventDefault();
                        region.scrollTop -= pageScrollAmount;
                        break;
                    case 'Home':
                        e.preventDefault();
                        region.scrollTop = 0;
                        break;
                    case 'End':
                        e.preventDefault();
                        region.scrollTop = region.scrollHeight;
                        break;
                }}
            }});
            
            // Announce scroll position to screen readers
            let scrollTimeout;
            region.addEventListener('scroll', () => {{
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {{
                    const progress = Math.round((region.scrollTop / (region.scrollHeight - region.clientHeight)) * 100);
                    region.setAttribute('aria-valuenow', progress);
                    if (progress === 0) {{
                        region.setAttribute('aria-label', 'At the beginning of content');
                    }} else if (progress === 100) {{
                        region.setAttribute('aria-label', 'At the end of content');
                    }} else {{
                        region.setAttribute('aria-label', `${progress}% scrolled`);
                    }}
                }}, 150);
            }});
        </script>
        """,
        height=int(max_height.replace("px", "")) + 40,
        key=f"scrollable_{key}"
    )
    
    return component_value

def custom_header_button(label, icon=None, key=None):
    """
    Create a custom header button with proper accessibility attributes.
    Uses Streamlit's component system for better integration.
    """
    component_value = components.html(
        f"""
        <button
            id="header-button-{key}"
            class="header-button"
            role="button"
            aria-label="{label}"
            title="{label}"
            style="
                min-height: 44px;
                padding: 8px 16px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                font-weight: 600;
                border-radius: 8px;
                cursor: pointer;
                background: linear-gradient(135deg, #2E7D32, #43A047);
                color: #FFFFFF;
                border: none;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                margin: 0.5rem;
            "
        >
            {f'<span aria-hidden="true" style="font-size: 1.2rem;">{icon}</span>' if icon else ''}
            <span style="font-size: 1rem;">{label}</span>
        </button>
        
        <style>
            .header-button:focus {{
                outline: 2px solid #2E7D32;
                outline-offset: 2px;
            }}
            
            .header-button:focus-visible {{
                box-shadow: 0 0 0 4px rgba(46, 125, 50, 0.2);
            }}
            
            .header-button:hover {{
                background: linear-gradient(135deg, #43A047, #2E7D32);
                transform: translateY(-2px);
            }}
            
            .header-button:active {{
                transform: translateY(1px);
            }}
        </style>
        
        <script>
            const button = document.getElementById('header-button-{key}');
            
            button.addEventListener('click', () => {{
                window.parent.postMessage({{
                    type: 'streamlit:message',
                    action: 'headerButtonClicked',
                    value: true,
                    key: '{key}'
                }}, '*');
            }});
            
            // Handle keyboard navigation
            button.addEventListener('keydown', (e) => {{
                if (e.key === 'Enter' || e.key === ' ') {{
                    e.preventDefault();
                    button.click();
                }}
            }});
        </script>
        """,
        height=60,
        key=f"header_button_{key}"
    )
    
    return component_value

def add_accessibility_support():
    """
    Add global accessibility support to the Streamlit app.
    """
    components.html(
        """
        <style>
            /* Ensure proper contrast */
            body {
                color: #1A1A1A;
            }
            
            /* Make interactive elements keyboard accessible */
            a:focus,
            button:focus,
            [role="button"]:focus,
            [tabindex="0"]:focus {
                outline: 2px solid #2E7D32;
                outline-offset: 2px;
            }
            
            /* Skip link for keyboard navigation */
            .skip-link {
                position: absolute;
                top: -40px;
                left: 0;
                background: #2E7D32;
                color: #FFFFFF;
                padding: 8px;
                z-index: 100;
                transition: top 0.3s ease;
            }
            
            .skip-link:focus {
                top: 0;
            }
            
            /* Ensure proper focus indication */
            *:focus-visible {
                outline: 2px solid #2E7D32;
                outline-offset: 2px;
            }
        </style>
        
        <a href="#main-content" class="skip-link">Skip to main content</a>
        
        <script>
            // Add keyboard navigation support
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    document.body.classList.add('keyboard-navigation');
                }
            });
            
            document.addEventListener('mousedown', () => {
                document.body.classList.remove('keyboard-navigation');
            });
        </script>
        """,
        height=0
    ) 