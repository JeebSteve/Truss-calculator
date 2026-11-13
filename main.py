from drafter import *
from dataclasses import dataclass, field
from typing import Dict
import math
import base64
'''
DATACLASS SECTION
****************************************
'''
@dataclass
class TrussMember:
    '''stores data for each independent bar of a truss'''
    id:str
    member_type:str
    length: float
    axial_force:float
    is_zero_force: bool

@dataclass
class State:
    '''state'''
    truss_type: str = 'Pratt'
    span_length:float = 12
    height: float
    num_bays:int
    num_joints:int
    applied_load:float
    distribute_load:bool
    members: Dict[str,TrussMember]
'''
FUNCTIONS!!!
********************************************'''


def draw_truss_visualizer(state: State) -> Image:
    """Generates the 2D SVG vector graphic and returns a native Drafter Image component."""
    width = 680
    height = 260
    margin = 55

    bays = state.num_bays
    span = state.span_length
    h = state.height
    bay_w = span / bays

    scale_x = (width - 2 * margin) / span
    scale_y = (height - 2 * margin) / h

    # 1. Calculate parametric node coordinates
    nodes_bot = []
    for i in range(bays + 1):
        x = margin + (i * bay_w * scale_x)
        y = height - margin
        nodes_bot.append((x, y))

    nodes_top = []
    for i in range(1, bays):
        x = margin + (i * bay_w * scale_x)
        y = height - margin - (h * scale_y)
        nodes_top.append((x, y))

    svg_elements = []

    # Background card rectangle inside the SVG
    bg_rect = '<rect x="0" y="0" width="%s" height="%s" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2" />' % (
        str(width), str(height)
    )
    svg_elements.append(bg_rect)

    # 2. Render Structural Members color-coded by axial force
    for m_id, m in state.members.items():
        idx = int(m_id.split("_")[1]) - 1

        if m_id.startswith("BC_"):
            p1, p2 = nodes_bot[idx], nodes_bot[idx + 1]
        elif m_id.startswith("TC_"):
            p1 = nodes_bot[0] if idx == 0 else nodes_top[idx - 1]
            p2 = nodes_bot[-1] if idx == bays - 1 else nodes_top[idx]
        elif m_id.startswith("VERT_"):
            if idx >= len(nodes_top):
                continue
            p1, p2 = nodes_bot[idx + 1], nodes_top[idx]
        else:  # Diagonals
            if state.truss_type == "Howe":
                p1 = nodes_bot[idx + 1]
                if idx == 0:
                    p2 = nodes_bot[0]
                elif idx == bays - 1:
                    p2 = nodes_top[idx - 1]
                else:
                    p2 = nodes_top[idx] if idx < bays // 2 else nodes_top[idx - 1]
            elif state.truss_type == "Warren":
                if idx == 0:
                    p1, p2 = nodes_bot[0], nodes_top[0]
                elif idx == bays - 1:
                    p1, p2 = nodes_top[-1], nodes_bot[-1]
                elif idx % 2 == 0:
                    p1, p2 = nodes_bot[idx], nodes_top[idx]
                else:
                    p1, p2 = nodes_top[idx - 1], nodes_bot[idx + 1]
            else:  # Pratt
                if idx == 0:
                    p1, p2 = nodes_bot[0], nodes_top[0]
                elif idx == bays - 1:
                    p1, p2 = nodes_top[-1], nodes_bot[-1]
                elif idx < bays // 2:
                    p1, p2 = nodes_bot[idx], nodes_top[idx]
                else:
                    p1, p2 = nodes_top[idx - 1], nodes_bot[idx + 1]

        if m.axial_force > 0:
            color = "#2563eb"
            stroke_w = "4"
        elif m.axial_force < 0:
            color = "#dc2626"
            stroke_w = "4"
        else:
            color = "#9ca3af"
            stroke_w = "2"

        line_tag = '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s" stroke-linecap="round" />' % (
            str(p1[0]), str(p1[1]), str(p2[0]), str(p2[1]), color, stroke_w
        )
        svg_elements.append(line_tag)

    # 3. Render Pin & Roller Supports
    left_x, left_y = nodes_bot[0]
    right_x, right_y = nodes_bot[-1]
    pin_support = '<polygon points="%s,%s %s,%s %s,%s" fill="#475569" />' % (
        str(left_x), str(left_y + 4), str(left_x - 10), str(left_y + 20), str(left_x + 10), str(left_y + 20)
    )
    roller_support = '<circle cx="%s" cy="%s" r="8" fill="#475569" />' % (str(right_x), str(right_y + 12))
    svg_elements.append(pin_support)
    svg_elements.append(roller_support)

    # 4. Render Joint Nodes & Force Labels
    for nx, ny in nodes_bot + nodes_top:
        node_tag = '<circle cx="%s" cy="%s" r="5" fill="#0f172a" stroke="#ffffff" stroke-width="1.5" />' % (str(nx), str(ny))
        svg_elements.append(node_tag)

    # 5. Built-in SVG Color Legend at the top-left
    legend_svg = (
        '<circle cx="25" cy="22" r="5" fill="#2563eb" />'
        '<text x="36" y="26" font-family="sans-serif" font-size="13" font-weight="bold" fill="#1e293b">Tension (+)</text>'
        '<circle cx="135" cy="22" r="5" fill="#dc2626" />'
        '<text x="146" y="26" font-family="sans-serif" font-size="13" font-weight="bold" fill="#1e293b">Compression (-)</text>'
        '<circle cx="275" cy="22" r="5" fill="#9ca3af" />'
        '<text x="286" y="26" font-family="sans-serif" font-size="13" font-weight="bold" fill="#1e293b">Zero-Force</text>'
    )
    svg_elements.append(legend_svg)

    svg_code = '<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s">\n%s\n</svg>' % (
        str(width), str(height), str(width), str(height), "\n".join(svg_elements)
    )

    # Encode SVG to Base64 so Drafter's Image() renders it cleanly without stripping tags
    svg_b64 = base64.b64encode(svg_code.encode("utf-8")).decode("utf-8")
    return Image("data:image/svg+xml;base64," + svg_b64)
 
def compute_truss(state: State) -> Dict[str, TrussMember]:
    """calculates all internal forces by using basic trigonometry"""
    members = dict()
    bay_width = state.span_length / state.num_bays
    diag_length = math.sqrt(bay_width**2 + state.height**2)
    theta = math.atan(state.height / bay_width)
    r_left = state.applied_load / 2.0

    # chords
    for i in range(1, state.num_bays + 1):
        bc_id = "BC_" + str(i)
        tc_id = "TC_" + str(i)
        diag_id = "DIAG_" + str(i)
        vert_id = "VERT_" + str(i)

        bot_force = r_left / math.tan(theta)
        top_force = -(r_left / math.sin(theta))

        members[bc_id] = TrussMember(bc_id, "bottom_chord", bay_width, bot_force, False)
        members[tc_id] = TrussMember(tc_id, "top_chord", bay_width, top_force, False)

        # web members
        if state.truss_type == "Pratt":
            diag_force = r_left / math.sin(theta)
            vert_force = -r_left
        elif state.truss_type == "Howe":
            diag_force = -(r_left / math.sin(theta))
            vert_force = r_left
        else:  # Warren Profile
            diag_force = r_left / math.sin(theta) if i % 2 != 0 else -(r_left / math.sin(theta))
            vert_force = 0.0

        members[diag_id] = TrussMember(diag_id, "diagonal", diag_length, diag_force, False)
        if vert_force != 0.0:
            members[vert_id] = TrussMember(vert_id, "vertical", state.height, vert_force, False)

    return members

''' ROUTES
***********************************
'''
#home
@route("/")
def index(state: State) -> Page:
    """Home view providing system overview and navigation."""
    return Page(state, [
        "## Civil Engineering Planar Truss Calculator",
        "**System Status:** " + state.feedback_message,
        Button("Configure Geometry & Loads", "/builder"),
        Button("View Theory & Presets", "/theory")
    ])


#user input
@route("/builder")
def builder(state: State) -> Page:
    """Inputs page containing SelectBox, TextBox, and CheckBox components."""
    return Page(state, [
        " Step 1: Input System Parameters",
        "Status: " + state.feedback_message,
        "Select Truss Profile Type:",
        SelectBox("truss_type", ["Pratt", "Howe", "Warren"], state.truss_type),
        "Total Span Length (m):",
        TextBox("span_length", str(state.span_length)),
        "Peak Height (m):",
        TextBox("height", str(state.height)),
        "Number of Bays / Panels (Must be an Even Number):",
        TextBox("num_bays", str(state.num_bays)),
        "Applied Downward Point Load (kN):",
        TextBox("applied_load", str(state.applied_load)),
        "Load Distribution Option:",
        CheckBox("distribute_load", state.distribute_load),
        Button("Calculate Statics & Forces", "/calculate")
    ])



@route("/calculate")
def run_analysis(
    state: State,
    truss_type: str,
    span_length: str,
    height: str,
    num_bays: str,
    applied_load: str,
    distribute_load: bool
) -> Page:
    """Validates inputs, processes formulas, updates state fields, and routes to results."""
    try:
        span = float(span_length)
        h = float(height)
        bays = int(num_bays)
        load = float(applied_load)
    except ValueError:
        state.feedback_message = "Error: Span, height, bays, and load must be valid numbers!"
        return builder(state)

    if span <= 0 or h <= 0 or load < 0:
        state.feedback_message = "Error: Span length, height, and load must be positive values!"
        return builder(state)
    if bays < 2 or bays % 2 != 0:
        state.feedback_message = "Error: Number of bays must be an even integer (minimum 2)."
        return builder(state)

   
    state.span_length = span
    state.height = h
    state.num_bays = bays
    state.applied_load = load
    state.truss_type = truss_type
    state.distribute_load = distribute_load
    state.num_joints = (2 * bays) + 2

    #shows calculations
    state.members = compute_truss(state)
    state.feedback_message = "Statics equilibrium calculated successfully!"

    return view_results(state)


# results page
@route("/results")
def view_results(state: State) -> Page:
    """Displays reaction summary, force distribution, and 2D SVG diagram."""
    tension_count = 0
    compression_count = 0
    total_length = 0.0
    max_force = 0.0
    critical_id = ""

    for m_id, m in state.members.items():
        total_length += m.length

        if m.axial_force > 0:
            tension_count += 1
        elif m.axial_force < 0:
            compression_count += 1

        if abs(m.axial_force) > max_force:
            max_force = abs(m.axial_force)
            critical_id = m_id

    diagram_html = draw_truss_visualizer(state)

    return Page(state, [
        "### Analysis Results & Force Schematic",
        diagram_html,
        "**Truss Profile:** %s | **Span:** %s m | **Height:** %s m" % (state.truss_type, str(state.span_length), str(state.height)),
        "**Total Joints:** %s | **Total Structural Members:** %s" % (str(state.num_joints), str(len(state.members))),
        "**Members in Tension (+):** %s | **Members in Compression (-):** %s" % (str(tension_count), str(compression_count)),
        "**Total Structural Steel Stock Length:** %.2f meters" % total_length,
        "**Critical Member (Max Stress):** %s carrying %.2f kN" % (critical_id, max_force),
        Button("View Detailed Member List Table", "/members"),
        Button("Re-configure Inputs", "/builder")
    ])


# results for each member
@route("/members")
def view_members(state: State) -> Page:
    """Breakdown table showing length, force, and state for every bar."""
    rows = ["ID | Category | Length (m) | Axial Force (kN) | Force State"]
    for m_id, m in state.members.items():
        status = "(+) TENSION" if m.axial_force > 0 else ("(-) COMPRESSION" if m.axial_force < 0 else "ZERO-FORCE")
        rows.append("%s | %s | %.2f | %.2f | %s" % (m.id, m.member_type, m.length, m.axial_force, status))

    return Page(state, [
        "### Individual Member Forces Breakdown",
        "\n".join(rows),
        Button("Back to Results Summary", "/results")
    ])


# theory page
@route("/theory")
def theory(state: State) -> Page:
    """Educational page explaining Pratt vs. Howe vs. Warren statics."""
    return Page(state, [
        "Civil Engineering Statics Reference",
        "Pratt Truss: Diagonals slope downward toward the center. Under gravity loads, diagonals act in TENSION while shorter verticals act in COMPRESSION.",
        "Howe Truss: Diagonals slope upward toward the center. Diagonals carry COMPRESSION while verticals carry TENSION.",
        "Warren Truss: Equilateral triangle arrangement that alternates tension and compression along adjacent web members.",
        Button("Return to Home View", "/"),
        Button("Reset Application Baseline", "/reset")
    ])


# reset button
@route("/reset")
def reset_app(state: State) -> Page:
    """Resets state fields back to default baseline configurations."""
    state.truss_type = "Pratt"
    state.span_length = 12.0
    state.height = 3.0
    state.num_bays = 4
    state.applied_load = 50.0
    state.distribute_load = False
    state.members = dict()
    state.feedback_message = "Application reset to default settings."
    return index(state)


start_server(State())
