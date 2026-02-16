"""
AI Chat Assistant for route optimization conversations.
Helps dispatchers understand decisions and make adjustments.
Includes tool calling to directly modify Dispatcher Sandbox.
"""

import anthropic
from typing import List, Dict, Optional, Tuple
import config
import json


def generate_mock_validation(keep, early, reschedule, cancel, vehicle_capacity, window_minutes):
    """
    Generate template-based validation for test mode (no API call).

    Args:
        keep: List of orders kept in route
        early: List of orders for early delivery
        reschedule: List of orders to reschedule
        cancel: List of orders to cancel
        vehicle_capacity: Vehicle capacity in units
        window_minutes: Delivery window in minutes

    Returns:
        str: Mock validation message
    """
    kept_units = sum(o.get('units', 0) for o in keep)
    capacity_pct = (kept_units / vehicle_capacity * 100) if vehicle_capacity > 0 else 0

    return f"""✅ Route validation (Test Mode - Mock Response):

**Capacity Check:**
- {len(keep)} orders kept ({kept_units}/{vehicle_capacity} units = {capacity_pct:.1f}%)
- Capacity constraint satisfied

**Order Disposition:**
- {len(keep)} orders on route
- {len(early)} orders for early delivery
- {len(reschedule)} orders to reschedule
- {len(cancel)} orders to cancel

**Time Estimate:**
- Estimated route time: {window_minutes} minutes (test mode uses simplified calculation)

**Test Mode Notice:** This is a mock validation. Enable AI (disable test mode) for detailed route analysis."""


def generate_mock_order_explanations(orders):
    """
    Generate generic explanations for test mode (no API call).

    Args:
        orders: List of orders needing explanations

    Returns:
        Dict mapping order_id to generic explanation
    """
    explanations = {}
    for order in orders:
        order_id = str(order.get('order_id', ''))
        category = order.get('category', 'UNKNOWN').upper()

        if category == 'KEEP':
            explanation = "Test mode - Order kept in optimized route"
        elif category == 'EARLY':
            explanation = "Test mode - Order eligible for early delivery"
        elif category == 'RESCHEDULE':
            explanation = "Test mode - Order recommended for rescheduling"
        elif category == 'CANCEL':
            explanation = "Test mode - Order recommended for cancellation"
        else:
            explanation = "Test mode - Generic reason"

        explanations[order_id] = explanation

    return explanations


def create_context_for_ai(keep, early, reschedule, cancel, valid_orders, time_matrix, vehicle_capacity, window_minutes, depot_address):
    """
    Create a comprehensive context string for the AI assistant.
    """
    # Calculate current route metrics
    kept_units = sum(o['units'] for o in keep)
    remaining_capacity = vehicle_capacity - kept_units

    # Calculate total route time
    total_route_time = 0
    if keep:
        sorted_keep = sorted(keep, key=lambda x: x.get('sequence_index', 0))
        kept_nodes = [k['node'] for k in sorted_keep]
        total_route_time = time_matrix[0][kept_nodes[0]]  # Depot to first
        for i in range(len(kept_nodes) - 1):
            total_route_time += time_matrix[kept_nodes[i]][kept_nodes[i + 1]]
        total_route_time += time_matrix[kept_nodes[-1]][0]  # Last to depot

    remaining_time = window_minutes - total_route_time

    # Create comprehensive context
    context = f"""You are an AI assistant helping a Buncha dispatcher understand and optimize delivery routes.

OPTIMIZATION CONFIGURATION:
===========================
- Fulfillment Location: {depot_address}
- Vehicle Capacity: {vehicle_capacity} units (Currently using: {kept_units} units, Remaining: {remaining_capacity} units)
- Delivery Window: {window_minutes} minutes (Route time: {total_route_time} min, Remaining: {remaining_time} min)
- Total Orders Processed: {len(valid_orders)}

COMPLETE ORDER DETAILS:
======================

KEPT ORDERS ({len(keep)} orders, {kept_units} units):
"""

    # Add detailed info for kept orders
    for order in sorted(keep, key=lambda x: x.get('sequence_index', 0)):
        context += f"\n- Order #{order['order_id']}: {order['customer_name']}"
        context += f"\n  Address: {order['delivery_address']}"
        context += f"\n  Units: {order['units']}"
        context += f"\n  Sequence: Stop #{order.get('sequence_index', 0) + 1}"
        context += f"\n  Est. Arrival: {order.get('estimated_arrival', 0)} min from start"
        context += f"\n  Status: KEPT - On optimized route"

    context += f"\n\nEARLY DELIVERY CANDIDATES ({len(early)} orders):"
    for order in early:
        # Find full order details from valid_orders
        full_order = next((o for o in valid_orders if o['order_id'] == order['order_id']), None)
        context += f"\n- Order #{order['order_id']}: {order['customer_name']}"
        context += f"\n  Address: {order['delivery_address']}"
        context += f"\n  Units: {order['units']}"
        if full_order:
            context += f"\n  Early Delivery OK: {'Yes' if full_order.get('early_delivery_ok') else 'No'}"
        context += f"\n  Status: EARLY - {order['reason']}"

    context += f"\n\nRESCHEDULE CANDIDATES ({len(reschedule)} orders):"
    for order in reschedule:
        full_order = next((o for o in valid_orders if o['order_id'] == order['order_id']), None)
        context += f"\n- Order #{order['order_id']}: {order['customer_name']}"
        context += f"\n  Address: {order['delivery_address']}"
        context += f"\n  Units: {order['units']}"
        context += f"\n  Status: RESCHEDULE - {order['reason']}"

    context += f"\n\nCANCEL RECOMMENDATIONS ({len(cancel)} orders):"
    for order in cancel:
        full_order = next((o for o in valid_orders if o['order_id'] == order['order_id']), None)
        context += f"\n- Order #{order['order_id']}: {order['customer_name']}"
        context += f"\n  Address: {order['delivery_address']}"
        context += f"\n  Units: {order['units']}"
        context += f"\n  Status: CANCEL - {order['reason']}"

    context += f"""

ROUTE CONSTRAINTS & METRICS:
============================
- Current route uses {kept_units}/{vehicle_capacity} units ({(kept_units/vehicle_capacity*100):.1f}% capacity)
- Current route time: {total_route_time}/{window_minutes} minutes ({(total_route_time/window_minutes*100):.1f}% of window)
- Spare capacity: {remaining_capacity} units
- Spare time: {remaining_time} minutes

YOUR ROLE & CAPABILITIES:
========================
You have access to tools that let you DIRECTLY MODIFY the Dispatcher Sandbox in response to user requests.

**Available Actions:**
1. **Move orders between categories** - Use modify_sandbox_order tool
   - KEEP: Add to route
   - EARLY: Move to early delivery
   - RESCHEDULE: Move to different window
   - CANCEL: Remove from delivery

2. **Check feasibility** - Use check_order_feasibility tool before adding orders
   - Validates capacity and time constraints
   - Provides detailed analysis

**When to Use Tools:**

**"Remove order #X" / "Take out order #X"**
→ Use modify_sandbox_order to move from KEEP to CANCEL/RESCHEDULE
→ Explain why (e.g., "Removed to free up capacity for other orders")

**"Add order #X back" / "Put order #X in the route"**
→ First use check_order_feasibility to validate
→ If feasible, use modify_sandbox_order to move to KEEP
→ If not feasible, explain why and suggest alternatives (remove other orders first)

**"Move order #X to early delivery"**
→ Use modify_sandbox_order to move to EARLY status
→ Confirm customer approved early delivery

**Question-Only Requests:**
**"Why is order #X not included?"**
→ Don't use tools, just explain the reason from the data above

**"What if I remove order #X?"**
→ Don't use tools, just calculate what would change

**IMPORTANT RULES:**
✅ USE TOOLS when dispatcher clearly wants to make changes ("remove", "add", "move")
✅ DON'T use tools for hypothetical questions ("what if", "can you", "would it")
✅ ALWAYS check feasibility before adding orders to KEEP
✅ Be specific about why you're making each change
✅ After using tools, explain what you did and the impact on capacity/time
✅ Changes you make with tools are IMMEDIATELY applied to the Dispatcher Sandbox
✅ Users can see updated map and metrics after you make changes
"""

    return context


def chat_with_assistant(messages: List[Dict[str, str]], context: str, api_key: str,
                        sandbox_data: Optional[Dict] = None, valid_orders: Optional[List[Dict]] = None,
                        time_matrix: Optional[List[List[int]]] = None,
                        vehicle_capacity: Optional[int] = None,
                        window_minutes: Optional[int] = None,
                        service_times: Optional[List[int]] = None) -> Tuple[str, Optional[Dict], List[str]]:
    """
    Send messages to Claude AI and get a response with tool calling support.

    Args:
        messages: List of message dicts with 'role' and 'content'
        context: System context about the optimization
        api_key: Anthropic API key
        sandbox_data: Optional sandbox data for tool execution
        valid_orders: Optional list of all valid orders
        time_matrix: Optional time matrix for feasibility checks
        vehicle_capacity: Optional vehicle capacity
        window_minutes: Optional delivery window in minutes
        service_times: Optional service times array

    Returns:
        Tuple of (response_text, updated_sandbox_data, tool_execution_messages)
    """
    if not api_key or api_key == "YOUR_ANTHROPIC_API_KEY_HERE":
        return "⚠️ Chat assistant is not configured. Please add your ANTHROPIC_API_KEY to the .env file to enable AI chat.", None, []

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Filter messages - API requires alternating user/assistant, starting with user
        # Skip any leading assistant messages (like our route explanation)
        api_messages = []
        for msg in messages:
            if len(api_messages) == 0 and msg["role"] == "assistant":
                # Skip leading assistant messages
                continue
            api_messages.append(msg)

        # If no messages to send, return empty
        if not api_messages:
            return "", None, []

        # Format system as list of content blocks
        system_blocks = [{"type": "text", "text": str(context)}]

        # Determine if tools should be available
        tools_available = (sandbox_data is not None and valid_orders is not None
                          and time_matrix is not None and vehicle_capacity is not None
                          and window_minutes is not None)

        # Tool execution tracking
        tool_executions = []
        updated_sandbox = sandbox_data.copy() if sandbox_data else None

        # Call Claude API with tool support
        while True:
            if tools_available:
                response = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=2000,
                    system=system_blocks,
                    tools=get_sandbox_tools(),
                    messages=api_messages
                )
            else:
                response = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=1500,
                    system=system_blocks,
                    messages=api_messages
                )

            # Check if we need to execute tools
            if response.stop_reason == "tool_use":
                # Find tool use blocks
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_use_id = block.id

                        # Execute the tool
                        if tool_name == "modify_sandbox_order":
                            success, message, updated_sandbox = execute_modify_sandbox_order(
                                tool_input['order_id'],
                                tool_input['new_status'],
                                tool_input['reason'],
                                updated_sandbox,
                                valid_orders,
                                time_matrix,
                                vehicle_capacity,
                                window_minutes,
                                service_times
                            )
                            tool_executions.append(message)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": message
                            })

                        elif tool_name == "check_order_feasibility":
                            feasibility_msg = execute_check_feasibility(
                                tool_input['order_id'],
                                updated_sandbox,
                                valid_orders,
                                time_matrix,
                                vehicle_capacity,
                                window_minutes,
                                service_times
                            )
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": feasibility_msg
                            })

                # Add assistant's message with tool use and our tool results to conversation
                api_messages.append({"role": "assistant", "content": response.content})
                api_messages.append({"role": "user", "content": tool_results})

                # Continue the loop to get Claude's final response
                continue

            else:
                # No more tool use, extract final text response
                final_text = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        final_text += block.text

                return final_text, updated_sandbox, tool_executions

    except Exception as e:
        return f"❌ Error communicating with AI assistant: {str(e)}", None, []


def validate_optimization_results(keep, early, reschedule, cancel, valid_orders, time_matrix,
                                   service_times, vehicle_capacity, window_minutes, api_key):
    """
    Use AI to validate optimization results and explain route logic.

    Returns:
        str: AI validation and explanation
    """
    # Check if AI is enabled (considers test mode and API key)
    if not config.is_ai_enabled():
        return generate_mock_validation(keep, early, reschedule, cancel, vehicle_capacity, window_minutes)

    if not api_key or api_key == "YOUR_ANTHROPIC_API_KEY_HERE":
        return None

    # Calculate actual totals for validation
    total_kept_units = sum(o["units"] for o in keep)

    # Calculate drive time and service time
    drive_time = 0
    if keep:
        sorted_keep = sorted(keep, key=lambda x: x.get('sequence_index', 0))
        kept_nodes = [k['node'] for k in sorted_keep]
        drive_time = time_matrix[0][kept_nodes[0]]
        for i in range(len(kept_nodes) - 1):
            drive_time += time_matrix[kept_nodes[i]][kept_nodes[i + 1]]
        drive_time += time_matrix[kept_nodes[-1]][0]

    total_service_time = 0
    if service_times:
        for order in keep:
            node = order["node"]
            if node < len(service_times):
                total_service_time += service_times[node]

    total_route_time = drive_time + total_service_time

    # Create validation prompt
    validation_prompt = f"""You are an expert logistics analyst reviewing an optimized delivery route.
Your job is to:
1. Validate the math and logic
2. Explain why this route makes the most sense
3. Flag any concerns or considerations

OPTIMIZATION RESULTS:
===================
Total Orders: {len(valid_orders)}
- KEPT: {len(keep)} orders ({total_kept_units} units)
- EARLY DELIVERY: {len(early)} orders
- RESCHEDULE: {len(reschedule)} orders
- CANCEL: {len(cancel)} orders

CONSTRAINTS:
- Vehicle Capacity: {vehicle_capacity} units
- Delivery Window: {window_minutes} minutes

ROUTE METRICS:
- Capacity Used: {total_kept_units}/{vehicle_capacity} units ({total_kept_units/vehicle_capacity*100:.1f}%)
- Drive Time: {drive_time} minutes
- Service Time: {total_service_time} minutes (unloading at {len(keep)} stops)
- Total Route Time: {total_route_time} minutes ({total_route_time/window_minutes*100:.1f}% of window)

KEPT ORDERS SEQUENCE:
"""

    for order in sorted(keep, key=lambda x: x.get('sequence_index', 0)):
        node = order["node"]
        service_time = service_times[node] if service_times and node < len(service_times) else 0
        validation_prompt += f"\n{order['sequence_index']+1}. Order #{order['order_id']}: {order['units']} units, {service_time} min service time"

    validation_prompt += f"""

DROPPED ORDERS:
- {len(early)} orders marked for early delivery (customer approved)
- {len(reschedule)} orders to reschedule (10-20 min from cluster)
- {len(cancel)} orders to cancel (>20 min from cluster)

YOUR TASK:
=========
1. **Validate Math**: Verify capacity ({total_kept_units} ≤ {vehicle_capacity}) and time ({total_route_time} ≤ {window_minutes})
2. **Check Logic**: Confirm dropped orders make sense given constraints
3. **Explain Route**: Why is THIS specific route optimal? What makes it better than alternatives?
4. **Flag Concerns**: Any edge cases, tight margins, or risks?

Provide a concise analysis (4-6 sentences) that helps the dispatcher understand and trust this route.
Focus on:
- Why we kept these {len(keep)} orders specifically
- Why we dropped the others
- Any tight constraints (capacity at {total_kept_units/vehicle_capacity*100:.0f}%, time at {total_route_time/window_minutes*100:.0f}%)
- Overall confidence in this route
"""

    try:
        client = anthropic.Anthropic(api_key=api_key)

        system_message = [{"type": "text", "text": "You are an expert logistics analyst validating delivery route optimizations."}]

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=800,
            system=system_message,
            messages=[{"role": "user", "content": validation_prompt}]
        )

        return response.content[0].text

    except Exception as e:
        return f"⚠️ Could not validate results: {str(e)}"


def execute_modify_sandbox_order(order_id: str, new_status: str, reason: str,
                                   sandbox_data: Dict, valid_orders: List[Dict],
                                   time_matrix: List[List[int]], vehicle_capacity: int,
                                   window_minutes: int, service_times: List[int]) -> Tuple[bool, str, Dict]:
    """
    Execute the modify_sandbox_order tool - move an order between categories.

    Returns:
        Tuple of (success, message, updated_sandbox_data)
    """
    # Find the order in all categories
    order_found = None
    current_status = None

    for status in ['keep', 'early', 'reschedule', 'cancel']:
        for order in sandbox_data.get(status, []):
            if str(order['order_id']) == str(order_id):
                order_found = order
                current_status = status.upper()
                break
        if order_found:
            break

    if not order_found:
        return False, f"❌ Order #{order_id} not found in any category.", sandbox_data

    # If already in target status, no change needed
    if current_status == new_status:
        return True, f"ℹ️ Order #{order_id} is already in {new_status} status.", sandbox_data

    # Check feasibility if moving to KEEP
    if new_status == "KEEP":
        # Calculate current capacity and time
        current_units = sum(o['units'] for o in sandbox_data.get('keep', []))
        order_units = order_found['units']

        if current_units + order_units > vehicle_capacity:
            return False, f"❌ Cannot add order #{order_id} to route: Would exceed capacity by {(current_units + order_units) - vehicle_capacity} units. Current: {current_units}/{vehicle_capacity} units.", sandbox_data

    # Remove from current category
    old_status_key = current_status.lower()
    sandbox_data[old_status_key] = [o for o in sandbox_data[old_status_key] if str(o['order_id']) != str(order_id)]

    # Prepare order for new category
    order_copy = order_found.copy()
    order_copy['reason'] = reason
    order_copy['category'] = new_status

    # If moving to KEEP, need to assign sequence and node
    if new_status == "KEEP":
        # Find the order in valid_orders to get its node
        node = None
        for idx, vo in enumerate(valid_orders):
            if str(vo['order_id']) == str(order_id):
                node = idx + 1  # Node 0 is depot
                break

        if node is None:
            return False, f"❌ Could not find order #{order_id} in valid orders list.", sandbox_data

        order_copy['node'] = node
        # Add to end of route
        current_keep = sandbox_data.get('keep', [])
        order_copy['sequence_index'] = len(current_keep)
        order_copy['estimated_arrival'] = 0  # Placeholder
    else:
        # Remove sequence info if not KEEP
        order_copy.pop('node', None)
        order_copy.pop('sequence_index', None)
        order_copy.pop('estimated_arrival', None)

    # Add to new category
    new_status_key = new_status.lower()
    if new_status_key not in sandbox_data:
        sandbox_data[new_status_key] = []
    sandbox_data[new_status_key].append(order_copy)

    # Success message
    action_verb = {
        "KEEP": "added to route",
        "EARLY": "moved to early delivery",
        "RESCHEDULE": "moved to reschedule",
        "CANCEL": "removed from route (cancelled)"
    }

    message = f"✅ Order #{order_id} {action_verb[new_status]}. {reason}"

    return True, message, sandbox_data


def execute_check_feasibility(order_id: str, sandbox_data: Dict, valid_orders: List[Dict],
                               time_matrix: List[List[int]], vehicle_capacity: int,
                               window_minutes: int, service_times: List[int]) -> str:
    """
    Check if adding an order to KEEP is feasible.

    Returns:
        str: Feasibility analysis message
    """
    # Find the order
    order_found = None
    for status in ['early', 'reschedule', 'cancel']:
        for order in sandbox_data.get(status, []):
            if str(order['order_id']) == str(order_id):
                order_found = order
                break
        if order_found:
            break

    if not order_found:
        # Check if already in KEEP
        for order in sandbox_data.get('keep', []):
            if str(order['order_id']) == str(order_id):
                return f"ℹ️ Order #{order_id} is already in the route (KEEP status)."
        return f"❌ Order #{order_id} not found."

    # Calculate current metrics
    current_units = sum(o['units'] for o in sandbox_data.get('keep', []))
    order_units = order_found['units']
    remaining_capacity = vehicle_capacity - current_units

    # Calculate current route time
    current_time = 0
    keep_orders = sandbox_data.get('keep', [])
    if keep_orders:
        sorted_keep = sorted(keep_orders, key=lambda x: x.get('sequence_index', 0))
        nodes = [o['node'] for o in sorted_keep]
        current_time = time_matrix[0][nodes[0]]
        for i in range(len(nodes) - 1):
            current_time += time_matrix[nodes[i]][nodes[i + 1]]
        current_time += time_matrix[nodes[-1]][0]

        # Add service times
        for o in sorted_keep:
            node = o['node']
            if node < len(service_times):
                current_time += service_times[node]

    remaining_time = window_minutes - current_time

    # Check capacity
    capacity_ok = order_units <= remaining_capacity
    capacity_msg = f"Capacity: {order_units} units needed, {remaining_capacity} units available"
    if not capacity_ok:
        capacity_msg += f" ❌ (exceeds by {order_units - remaining_capacity} units)"
    else:
        capacity_msg += " ✅"

    # Estimate time needed (rough estimate)
    # Find order node
    order_node = None
    for idx, vo in enumerate(valid_orders):
        if str(vo['order_id']) == str(order_id):
            order_node = idx + 1
            break

    if order_node:
        # Rough estimate: distance from depot + service time
        depot_distance = time_matrix[0][order_node]
        service_time = service_times[order_node] if order_node < len(service_times) else 3
        estimated_time = depot_distance * 2 + service_time  # Rough round trip

        time_ok = estimated_time <= remaining_time
        time_msg = f"Time: ~{estimated_time} min estimated (round trip), {remaining_time} min available"
        if not time_ok:
            time_msg += f" ❌ (exceeds by ~{estimated_time - remaining_time} min)"
        else:
            time_msg += " ✅"
    else:
        time_msg = "Time: Could not estimate (order node not found)"
        time_ok = False

    # Overall feasibility
    if capacity_ok and time_ok:
        verdict = f"\n\n✅ **FEASIBLE**: Order #{order_id} can likely be added to the route.\n{capacity_msg}\n{time_msg}\n\nNote: This is an estimate. Actual route time depends on optimal sequencing."
    elif capacity_ok:
        verdict = f"\n\n⚠️ **QUESTIONABLE**: Order #{order_id} might fit, but time is tight.\n{capacity_msg}\n{time_msg}\n\nConsider removing another order first to free up time."
    else:
        verdict = f"\n\n❌ **NOT FEASIBLE**: Order #{order_id} cannot be added.\n{capacity_msg}\n{time_msg}\n\nYou must remove other orders first to free up capacity."

    return verdict


def get_suggested_questions() -> List[str]:
    """Return a list of suggested questions dispatchers might ask."""
    return [
        "Why was order #70592 kept in the route?",
        "Can you add back order #70610?",
        "Remove order #70509 from the route",
        "Why are some orders recommended for cancellation?",
        "How can I fit more orders in this route?",
        "Which rescheduled orders are closest to the current route?",
    ]


def get_sandbox_tools() -> List[Dict]:
    """
    Define tools the AI can use to modify the Dispatcher Sandbox.
    """
    return [
        {
            "name": "modify_sandbox_order",
            "description": "Move an order between categories (KEEP, EARLY, RESCHEDULE, CANCEL) in the Dispatcher Sandbox. Use this when the dispatcher asks to add, remove, or move orders.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to modify (e.g., '70509')"
                    },
                    "new_status": {
                        "type": "string",
                        "enum": ["KEEP", "EARLY", "RESCHEDULE", "CANCEL"],
                        "description": "The new status for the order. KEEP = include in route, EARLY = deliver early, RESCHEDULE = move to different window, CANCEL = don't deliver"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation of why this change is being made (for audit trail)"
                    }
                },
                "required": ["order_id", "new_status", "reason"]
            }
        },
        {
            "name": "check_order_feasibility",
            "description": "Check if adding an order to the route is feasible given current capacity and time constraints. Use this before moving an order to KEEP status.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to check"
                    }
                },
                "required": ["order_id"]
            }
        }
    ]


def generate_order_explanations(keep, early, reschedule, cancel, time_matrix, depot_address, api_key):
    """
    Use AI to generate specific, detailed explanations for each order's disposition.

    Args:
        keep: List of orders kept in route
        early: List of orders for early delivery
        reschedule: List of orders to reschedule
        cancel: List of orders to cancel
        time_matrix: Travel time matrix
        depot_address: Depot location
        api_key: Anthropic API key

    Returns:
        Dict mapping order_id to AI-generated explanation
    """
    # Check if AI is enabled (considers test mode and API key)
    if not config.is_ai_enabled():
        all_orders = keep + early + reschedule + cancel
        return generate_mock_order_explanations(all_orders)

    if not api_key or api_key == "YOUR_ANTHROPIC_API_KEY_HERE":
        # Return None if AI not configured - will use default reasons
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Build comprehensive prompt with all order details
        prompt = f"""You are a logistics expert explaining route optimization decisions to a dispatcher.

CONTEXT:
- Fulfillment Location: {depot_address}
- Total orders processed: {len(keep) + len(early) + len(reschedule) + len(cancel)}
- Orders kept in route: {len(keep)}
- Orders for alternate handling: {len(early) + len(reschedule) + len(cancel)}

ORDERS KEPT IN ROUTE:
"""

        for order in keep:
            node = order['node']
            depot_dist = time_matrix[0][node]
            prompt += f"\n- Order #{order['order_id']}: {order['customer_name']}, {order['units']} units"
            prompt += f"\n  Stop #{order['sequence_index']+1}, {depot_dist} min from depot"
            prompt += f"\n  Optimal Score: {order.get('optimal_score', 'N/A')}/100"

        prompt += f"\n\nEARLY DELIVERY CANDIDATES ({len(early)} orders):"
        for order in early:
            prompt += f"\n- Order #{order['order_id']}: {order['customer_name']}, {order['units']} units"
            prompt += f"\n  Address: {order['delivery_address']}"
            prompt += f"\n  Optimal Score: {order.get('optimal_score', 'N/A')}/100"

        prompt += f"\n\nRESCHEDULE CANDIDATES ({len(reschedule)} orders):"
        for order in reschedule:
            prompt += f"\n- Order #{order['order_id']}: {order['customer_name']}, {order['units']} units"
            prompt += f"\n  Address: {order['delivery_address']}"
            prompt += f"\n  Optimal Score: {order.get('optimal_score', 'N/A')}/100"

        prompt += f"\n\nCANCEL RECOMMENDATIONS ({len(cancel)} orders):"
        for order in cancel:
            prompt += f"\n- Order #{order['order_id']}: {order['customer_name']}, {order['units']} units"
            prompt += f"\n  Address: {order['delivery_address']}"
            prompt += f"\n  Optimal Score: {order.get('optimal_score', 'N/A')}/100"

        prompt += """

YOUR TASK:
Generate a brief, specific explanation (1-2 sentences) for EACH order explaining why it received its disposition.

Format your response EXACTLY as follows (one line per order):
ORDER_ID|explanation text here

Examples:
70509|Kept in route - optimal position in cluster, minimizes total drive time while fitting capacity constraints.
70592|Recommended for early delivery - only 8 minutes from route cluster and customer approved early delivery.
70610|Recommended for rescheduling - 15 minutes from cluster, would add significant time but could fit in adjacent window.
70611|Recommended for cancellation - 25+ minutes from route cluster, cost to serve exceeds delivery value.

Generate explanations for ALL orders listed above. Be specific about:
- Geographic reasoning (distances, cluster positioning)
- Efficiency factors (units delivered, time added)
- Constraint impacts (capacity, time window)
- Strategic recommendations (why this disposition makes business sense)

Format: ORDER_ID|explanation (one per line, no extra text)
"""

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response into dict
        explanations = {}
        response_text = response.content[0].text.strip()

        for line in response_text.split('\n'):
            line = line.strip()
            if '|' in line:
                parts = line.split('|', 1)
                if len(parts) == 2:
                    order_id = parts[0].strip()
                    explanation = parts[1].strip()
                    explanations[order_id] = explanation

        return explanations

    except Exception as e:
        print(f"Error generating order explanations: {e}")
        return None


def call_claude_api(prompt: str, api_key: str = None) -> str:
    """
    Simple helper function to call Claude API with a single prompt.
    Used for validation and analysis tasks.

    Args:
        prompt: The prompt to send to Claude
        api_key: Anthropic API key (optional, will use config if not provided)

    Returns:
        Claude's response text
    """
    if api_key is None:
        api_key = config.get_anthropic_api_key()

    if not api_key or api_key == "YOUR_ANTHROPIC_API_KEY_HERE":
        return "⚠️ AI assistant is not configured. Please add your ANTHROPIC_API_KEY to the .env file."

    try:
        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text

    except Exception as e:
        return f"⚠️ Error calling Claude API: {str(e)}"
