import plotly.graph_objects as go
import plotly.express as px
import json

# Data from the provided JSON
data = {
    "steps": [
        {"id": 1, "name": "Load Configuration", "type": "setup", "description": "Load config.json & .env files"},
        {"id": 2, "name": "Setup Chrome WebDriver", "type": "setup", "description": "Initialize Selenium WebDriver"},
        {"id": 3, "name": "Open quantman.in", "type": "action", "description": "Navigate to website"},
        {"id": 4, "name": "Select Flattrade Broker", "type": "action", "description": "Choose broker option"},
        {"id": 5, "name": "Fill Login Details", "type": "action", "description": "Username, password, PIN"},
        {"id": 6, "name": "Generate TOTP Code", "type": "action", "description": "Using pyotp library"},
        {"id": 7, "name": "Fill TOTP & Submit", "type": "action", "description": "Enter TOTP and submit form"},
        {"id": 8, "name": "Check Login Status", "type": "verification", "description": "Verify success/failure"},
        {"id": 9, "name": "Send Notifications", "type": "verification", "description": "WhatsApp/SMS via Twilio"},
        {"id": 10, "name": "Cleanup Resources", "type": "cleanup", "description": "Close browser and log"}
    ]
}

# Color mapping for different step types
color_map = {
    'setup': '#1FB8CD',      # Blue for setup
    'action': '#ECEBD5',     # Green for actions  
    'verification': '#FFC185', # Orange for verification
    'cleanup': '#B4413C'     # Red for cleanup
}

# Create the flowchart
fig = go.Figure()

# Add main workflow steps (1-8)
for i, step in enumerate(data['steps'][:8]):
    y_pos = 10 - i  # Reverse order for top-to-bottom flow
    
    # Add step boxes
    fig.add_shape(
        type="rect",
        x0=-1.5, y0=y_pos-0.3, x1=1.5, y1=y_pos+0.3,
        fillcolor=color_map[step['type']],
        line=dict(color="black", width=2)
    )
    
    # Add step text (use full names, abbreviate if needed)
    step_text = step['name']
    if step_text == "Setup Chrome WebDriver":
        step_text = "Setup WebDriver"
    elif step_text == "Select Flattrade Broker":
        step_text = "Select Broker"
    elif step_text == "Generate TOTP Code":
        step_text = "Generate TOTP"
    elif step_text == "Fill TOTP & Submit":
        step_text = "Fill TOTP"
    elif step_text == "Check Login Status":
        step_text = "Check Status"
    elif step_text == "Load Configuration":
        step_text = "Load Config"
    
    fig.add_annotation(
        x=0, y=y_pos,
        text=f"{step['id']}. {step_text}",
        showarrow=False,
        font=dict(size=13, color="black")
    )
    
    # Add arrows between steps (except for the last step)
    if i < 7:
        fig.add_annotation(
            x=0, y=y_pos-0.5,
            text="↓",
            showarrow=False,
            font=dict(size=20, color="black")
        )

# Add decision diamond for login success after step 8
decision_y = 1.5
fig.add_shape(
    type="path",
    path=f"M 0 {decision_y-0.8} L 0.8 {decision_y-0.4} L 0 {decision_y} L -0.8 {decision_y-0.4} Z",
    fillcolor="#FFC185",
    line=dict(color="black", width=2)
)

fig.add_annotation(
    x=0, y=decision_y-0.4,
    text="Login Success?",
    showarrow=False,
    font=dict(size=12, color="black")
)

# Add arrow from step 8 to decision
fig.add_annotation(
    x=0, y=decision_y+0.5,
    text="↓",
    showarrow=False,
    font=dict(size=20, color="black")
)

# Add success notification branch (Yes path)
fig.add_shape(
    type="rect",
    x0=2.2, y0=decision_y-0.7, x1=4.2, y1=decision_y-0.1,
    fillcolor="#ECEBD5",
    line=dict(color="green", width=2)
)

fig.add_annotation(
    x=3.2, y=decision_y-0.4,
    text="Success Notif",
    showarrow=False,
    font=dict(size=12, color="black")
)

# Add failure notification branch (No path)
fig.add_shape(
    type="rect",
    x0=-4.2, y0=decision_y-0.7, x1=-2.2, y1=decision_y-0.1,
    fillcolor="#DB4545",
    line=dict(color="white", width=2)
)

fig.add_annotation(
    x=-3.2, y=decision_y-0.4,
    text="Fail Notif",
    showarrow=False,
    font=dict(size=12, color="white")
)

# Add Yes/No labels with better visibility
fig.add_annotation(
    x=1.4, y=decision_y-0.2,
    text="Yes",
    showarrow=False,
    font=dict(size=14, color="green"),
    bgcolor="white",
    bordercolor="green",
    borderwidth=1
)

fig.add_annotation(
    x=-1.4, y=decision_y-0.2,
    text="No",
    showarrow=False,
    font=dict(size=14, color="red"),
    bgcolor="white",
    bordercolor="red",
    borderwidth=1
)

# Add arrows to notification boxes
fig.add_annotation(
    x=1.8, y=decision_y-0.4,
    text="→",
    showarrow=False,
    font=dict(size=18, color="green")
)

fig.add_annotation(
    x=-1.8, y=decision_y-0.4,
    text="←",
    showarrow=False,
    font=dict(size=18, color="red")
)

# Add cleanup step at the bottom (single instance)
cleanup_y = -0.5
fig.add_shape(
    type="rect",
    x0=-1.5, y0=cleanup_y-0.3, x1=1.5, y1=cleanup_y+0.3,
    fillcolor=color_map['cleanup'],
    line=dict(color="black", width=2)
)

fig.add_annotation(
    x=0, y=cleanup_y,
    text="10. Cleanup Res",
    showarrow=False,
    font=dict(size=13, color="white")
)

# Add arrows from notification boxes to cleanup
fig.add_annotation(
    x=3.2, y=cleanup_y+1.2,
    text="↓",
    showarrow=False,
    font=dict(size=20, color="black")
)

fig.add_annotation(
    x=-3.2, y=cleanup_y+1.2,
    text="↓",
    showarrow=False,
    font=dict(size=20, color="black")
)

# Add connecting lines from notifications to cleanup
fig.add_shape(
    type="line",
    x0=3.2, y0=decision_y-0.7, x1=3.2, y1=cleanup_y+1.5,
    line=dict(color="black", width=2)
)

fig.add_shape(
    type="line",
    x0=-3.2, y0=decision_y-0.7, x1=-3.2, y1=cleanup_y+1.5,
    line=dict(color="black", width=2)
)

fig.add_shape(
    type="line",
    x0=-3.2, y0=cleanup_y+1.5, x1=3.2, y1=cleanup_y+1.5,
    line=dict(color="black", width=2)
)

fig.add_shape(
    type="line",
    x0=0, y0=cleanup_y+1.5, x1=0, y1=cleanup_y+0.3,
    line=dict(color="black", width=2)
)

# Update layout
fig.update_layout(
    title="Python Automation Workflow",
    xaxis=dict(range=[-5, 5], showgrid=False, showticklabels=False, zeroline=False),
    yaxis=dict(range=[-1.5, 11.5], showgrid=False, showticklabels=False, zeroline=False),
    showlegend=False
)

# Save the chart
fig.write_image("workflow_chart.png")