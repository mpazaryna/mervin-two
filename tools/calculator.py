"""
Calculator Tool

Provides basic arithmetic operations for the MCP Learning Server.
This tool demonstrates parameter validation, error handling, and
comprehensive mathematical operations.
"""

import math
from typing import Union

from .registry import tool


@tool(
    name="calculator",
    description="Perform basic arithmetic operations",
    parameter_schema={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide", "power", "sqrt", "abs"],
                "description": "Arithmetic operation to perform"
            },
            "a": {
                "type": "number",
                "description": "First number"
            },
            "b": {
                "type": "number",
                "description": "Second number (not required for sqrt and abs operations)"
            }
        },
        "required": ["operation", "a"]
    },
    return_schema={
        "type": "number",
        "description": "Result of the arithmetic operation"
    },
    examples=[
        {"operation": "add", "a": 5, "b": 3, "result": 8},
        {"operation": "multiply", "a": 4, "b": 7, "result": 28},
        {"operation": "divide", "a": 10, "b": 2, "result": 5},
        {"operation": "sqrt", "a": 16, "result": 4},
        {"operation": "power", "a": 2, "b": 3, "result": 8}
    ],
    category="math"
)
def calculator(operation: str, a: Union[int, float], b: Union[int, float] = None) -> float:
    """
    Perform arithmetic operations.
    
    Args:
        operation: The operation to perform
        a: First number
        b: Second number (optional for some operations)
        
    Returns:
        Result of the operation
        
    Raises:
        ValueError: For invalid operations or parameters
    """
    # Convert inputs to float for consistent handling
    a = float(a)
    if b is not None:
        b = float(b)
    
    if operation == "add":
        if b is None:
            raise ValueError("Addition requires two numbers")
        return a + b
    
    elif operation == "subtract":
        if b is None:
            raise ValueError("Subtraction requires two numbers")
        return a - b
    
    elif operation == "multiply":
        if b is None:
            raise ValueError("Multiplication requires two numbers")
        return a * b
    
    elif operation == "divide":
        if b is None:
            raise ValueError("Division requires two numbers")
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    elif operation == "power":
        if b is None:
            raise ValueError("Power operation requires two numbers")
        return a ** b
    
    elif operation == "sqrt":
        if a < 0:
            raise ValueError("Cannot take square root of negative number")
        return math.sqrt(a)
    
    elif operation == "abs":
        return abs(a)
    
    else:
        raise ValueError(f"Unknown operation: {operation}")


@tool(
    name="advanced_calculator",
    description="Perform advanced mathematical operations",
    parameter_schema={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["sin", "cos", "tan", "log", "ln", "factorial", "gcd", "lcm"],
                "description": "Advanced mathematical operation to perform"
            },
            "a": {
                "type": "number",
                "description": "First number"
            },
            "b": {
                "type": "number",
                "description": "Second number (required for gcd and lcm operations)"
            },
            "angle_unit": {
                "type": "string",
                "enum": ["radians", "degrees"],
                "default": "radians",
                "description": "Unit for trigonometric functions"
            }
        },
        "required": ["operation", "a"]
    },
    return_schema={
        "type": "number",
        "description": "Result of the advanced mathematical operation"
    },
    examples=[
        {"operation": "sin", "a": 1.5708, "angle_unit": "radians", "result": 1.0},
        {"operation": "log", "a": 100, "result": 2.0},
        {"operation": "factorial", "a": 5, "result": 120},
        {"operation": "gcd", "a": 48, "b": 18, "result": 6}
    ],
    category="math"
)
def advanced_calculator(operation: str, a: Union[int, float], 
                       b: Union[int, float] = None, 
                       angle_unit: str = "radians") -> float:
    """
    Perform advanced mathematical operations.
    
    Args:
        operation: The operation to perform
        a: First number
        b: Second number (optional for some operations)
        angle_unit: Unit for trigonometric functions
        
    Returns:
        Result of the operation
        
    Raises:
        ValueError: For invalid operations or parameters
    """
    a = float(a)
    if b is not None:
        b = float(b)
    
    if operation in ["sin", "cos", "tan"]:
        # Convert degrees to radians if needed
        angle = a
        if angle_unit == "degrees":
            angle = math.radians(a)
        
        if operation == "sin":
            return math.sin(angle)
        elif operation == "cos":
            return math.cos(angle)
        elif operation == "tan":
            return math.tan(angle)
    
    elif operation == "log":
        if a <= 0:
            raise ValueError("Logarithm requires positive number")
        return math.log10(a)
    
    elif operation == "ln":
        if a <= 0:
            raise ValueError("Natural logarithm requires positive number")
        return math.log(a)
    
    elif operation == "factorial":
        if a < 0 or a != int(a):
            raise ValueError("Factorial requires non-negative integer")
        return float(math.factorial(int(a)))
    
    elif operation == "gcd":
        if b is None:
            raise ValueError("GCD requires two numbers")
        return float(math.gcd(int(a), int(b)))
    
    elif operation == "lcm":
        if b is None:
            raise ValueError("LCM requires two numbers")
        return float(abs(int(a) * int(b)) // math.gcd(int(a), int(b)))
    
    else:
        raise ValueError(f"Unknown operation: {operation}")


@tool(
    name="calculator_help",
    description="Get help and examples for calculator operations",
    parameter_schema={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "description": "Specific operation to get help for (optional)"
            }
        }
    },
    return_schema={
        "type": "string",
        "description": "Help text for calculator operations"
    },
    category="help"
)
def calculator_help(operation: str = None) -> str:
    """
    Get help for calculator operations.
    
    Args:
        operation: Specific operation to get help for
        
    Returns:
        Help text
    """
    if operation:
        # Specific operation help
        help_texts = {
            "add": "Addition: calculator(operation='add', a=5, b=3) → 8",
            "subtract": "Subtraction: calculator(operation='subtract', a=10, b=4) → 6",
            "multiply": "Multiplication: calculator(operation='multiply', a=6, b=7) → 42",
            "divide": "Division: calculator(operation='divide', a=15, b=3) → 5",
            "power": "Exponentiation: calculator(operation='power', a=2, b=3) → 8",
            "sqrt": "Square root: calculator(operation='sqrt', a=16) → 4",
            "abs": "Absolute value: calculator(operation='abs', a=-5) → 5",
            "sin": "Sine: advanced_calculator(operation='sin', a=1.5708) → 1.0",
            "cos": "Cosine: advanced_calculator(operation='cos', a=0) → 1.0",
            "tan": "Tangent: advanced_calculator(operation='tan', a=0.7854) → 1.0",
            "log": "Base-10 logarithm: advanced_calculator(operation='log', a=100) → 2.0",
            "ln": "Natural logarithm: advanced_calculator(operation='ln', a=2.718) → 1.0",
            "factorial": "Factorial: advanced_calculator(operation='factorial', a=5) → 120",
            "gcd": "Greatest common divisor: advanced_calculator(operation='gcd', a=48, b=18) → 6",
            "lcm": "Least common multiple: advanced_calculator(operation='lcm', a=12, b=18) → 36"
        }
        return help_texts.get(operation, f"No help available for operation: {operation}")
    
    # General help
    return """Calculator Tools Help:

Basic Operations (calculator tool):
- add: Add two numbers
- subtract: Subtract second number from first
- multiply: Multiply two numbers
- divide: Divide first number by second
- power: Raise first number to the power of second
- sqrt: Square root of a number
- abs: Absolute value of a number

Advanced Operations (advanced_calculator tool):
- sin, cos, tan: Trigonometric functions
- log: Base-10 logarithm
- ln: Natural logarithm
- factorial: Factorial of a number
- gcd: Greatest common divisor of two numbers
- lcm: Least common multiple of two numbers

Examples:
- calculator(operation='add', a=5, b=3) → 8
- calculator(operation='sqrt', a=16) → 4
- advanced_calculator(operation='sin', a=90, angle_unit='degrees') → 1.0

Use calculator_help(operation='<operation_name>') for specific operation help."""
