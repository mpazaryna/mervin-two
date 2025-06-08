"""
Test Tools Implementation
"""

import pytest
import json
import math
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.registry import ToolRegistry, registry
from tools.calculator import calculator, advanced_calculator, calculator_help
from tools.utilities import echo, time_tool, random_generator, text_processor, json_formatter


class TestToolRegistry:
    """Test the tool registry system."""
    
    def setup_method(self):
        """Setup test registry."""
        self.test_registry = ToolRegistry()
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        assert len(self.test_registry.tools) == 0
        assert len(self.test_registry.categories) == 0
    
    def test_tool_registration(self):
        """Test tool registration."""
        @self.test_registry.register(
            name="test_tool",
            description="A test tool",
            category="test"
        )
        def test_function(x: int) -> int:
            return x * 2
        
        assert "test_tool" in self.test_registry.tools
        assert "test" in self.test_registry.categories
        assert "test_tool" in self.test_registry.categories["test"]
        
        tool_def = self.test_registry.get_tool("test_tool")
        assert tool_def.name == "test_tool"
        assert tool_def.description == "A test tool"
        assert tool_def.category == "test"
    
    def test_parameter_schema_generation(self):
        """Test automatic parameter schema generation."""
        @self.test_registry.register(
            name="schema_test",
            description="Schema test"
        )
        def schema_function(name: str, age: int, height: float = 1.8) -> str:
            return f"{name} is {age} years old"
        
        tool_def = self.test_registry.get_tool("schema_test")
        schema = tool_def.parameter_schema
        
        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
        assert "height" in schema["properties"]
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["age"]["type"] == "integer"
        assert schema["properties"]["height"]["type"] == "number"
        assert "name" in schema["required"]
        assert "age" in schema["required"]
        assert "height" not in schema["required"]  # Has default value
    
    def test_tool_execution(self):
        """Test tool execution."""
        @self.test_registry.register(
            name="multiply",
            description="Multiply two numbers"
        )
        def multiply(a: int, b: int) -> int:
            return a * b
        
        result = self.test_registry.execute_tool("multiply", {"a": 5, "b": 3})
        assert result == 15
    
    def test_tool_validation(self):
        """Test parameter validation."""
        @self.test_registry.register(
            name="validate_test",
            description="Validation test"
        )
        def validate_function(required_param: str, optional_param: int = 10) -> str:
            return f"{required_param}:{optional_param}"
        
        # Valid call
        result = self.test_registry.execute_tool("validate_test", {"required_param": "test"})
        assert result == "test:10"
        
        # Missing required parameter
        with pytest.raises(ValueError, match="Missing required parameter"):
            self.test_registry.execute_tool("validate_test", {})
    
    def test_list_tools(self):
        """Test listing tools."""
        @self.test_registry.register(name="tool1", description="Tool 1", category="cat1")
        def tool1(): pass
        
        @self.test_registry.register(name="tool2", description="Tool 2", category="cat2")
        def tool2(): pass
        
        tools = self.test_registry.list_tools()
        assert len(tools) == 2
        
        tool_names = [tool["name"] for tool in tools]
        assert "tool1" in tool_names
        assert "tool2" in tool_names
    
    def test_get_tool_help(self):
        """Test getting tool help."""
        @self.test_registry.register(
            name="help_test",
            description="Help test tool",
            examples=[{"input": "test", "output": "result"}]
        )
        def help_function(param: str) -> str:
            return param
        
        help_text = self.test_registry.get_tool_help("help_test")
        assert "help_test" in help_text
        assert "Help test tool" in help_text
        assert "param" in help_text


class TestCalculatorTool:
    """Test calculator tool functionality."""
    
    def test_basic_operations(self):
        """Test basic arithmetic operations."""
        assert calculator("add", 5, 3) == 8
        assert calculator("subtract", 10, 4) == 6
        assert calculator("multiply", 6, 7) == 42
        assert calculator("divide", 15, 3) == 5
        assert calculator("power", 2, 3) == 8
    
    def test_single_operand_operations(self):
        """Test operations with single operand."""
        assert calculator("sqrt", 16) == 4
        assert calculator("abs", -5) == 5
        assert calculator("abs", 5) == 5
    
    def test_division_by_zero(self):
        """Test division by zero error."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calculator("divide", 10, 0)
    
    def test_sqrt_negative(self):
        """Test square root of negative number."""
        with pytest.raises(ValueError, match="Cannot take square root of negative number"):
            calculator("sqrt", -4)
    
    def test_missing_second_operand(self):
        """Test operations that require two operands."""
        with pytest.raises(ValueError, match="requires two numbers"):
            calculator("add", 5)
    
    def test_unknown_operation(self):
        """Test unknown operation."""
        with pytest.raises(ValueError, match="Unknown operation"):
            calculator("unknown", 5, 3)
    
    def test_advanced_operations(self):
        """Test advanced mathematical operations."""
        # Trigonometric functions
        assert abs(advanced_calculator("sin", math.pi/2) - 1.0) < 1e-10
        assert abs(advanced_calculator("cos", 0) - 1.0) < 1e-10
        
        # Logarithms
        assert abs(advanced_calculator("log", 100) - 2.0) < 1e-10
        assert abs(advanced_calculator("ln", math.e) - 1.0) < 1e-10
        
        # Factorial
        assert advanced_calculator("factorial", 5) == 120
        
        # GCD and LCM
        assert advanced_calculator("gcd", 48, 18) == 6
        assert advanced_calculator("lcm", 12, 18) == 36
    
    def test_angle_units(self):
        """Test trigonometric functions with different angle units."""
        # Test degrees
        assert abs(advanced_calculator("sin", 90, angle_unit="degrees") - 1.0) < 1e-10
        assert abs(advanced_calculator("cos", 90, angle_unit="degrees") - 0.0) < 1e-10
    
    def test_calculator_help(self):
        """Test calculator help function."""
        help_text = calculator_help()
        assert "Calculator Tools Help" in help_text
        assert "add" in help_text
        assert "multiply" in help_text
        
        # Specific operation help
        add_help = calculator_help("add")
        assert "Addition" in add_help
        assert "calculator(operation='add'" in add_help


class TestUtilityTools:
    """Test utility tools functionality."""
    
    def test_echo_basic(self):
        """Test basic echo functionality."""
        assert echo("Hello World") == "Hello World"
        assert echo("Test", repeat=3) == "Test\nTest\nTest"
        assert echo("Hi", prefix="Echo: ") == "Echo: Hi"
        assert echo("Bye", suffix="!") == "Bye!"
        assert echo("Test", prefix="[", suffix="]") == "[Test]"
    
    def test_echo_validation(self):
        """Test echo parameter validation."""
        with pytest.raises(ValueError, match="Repeat count must be between 1 and 10"):
            echo("test", repeat=0)
        
        with pytest.raises(ValueError, match="Repeat count must be between 1 and 10"):
            echo("test", repeat=11)
    
    def test_time_tool(self):
        """Test time tool functionality."""
        # Test different formats
        iso_time = time_tool("iso")
        assert "T" in iso_time  # ISO format contains T
        
        unix_time = time_tool("unix")
        assert unix_time.isdigit()  # Unix timestamp is numeric
        
        human_time = time_tool("human")
        assert "-" in human_time and ":" in human_time  # Human format has date and time
        
        # Test custom format
        custom_time = time_tool("custom", custom_format="%Y-%m-%d")
        assert len(custom_time) == 10  # YYYY-MM-DD format
    
    def test_time_tool_validation(self):
        """Test time tool validation."""
        with pytest.raises(ValueError, match="custom_format is required"):
            time_tool("custom")
        
        with pytest.raises(ValueError, match="Unknown time format"):
            time_tool("invalid")
    
    def test_random_generator(self):
        """Test random generator functionality."""
        # Test integer generation
        rand_int = random_generator("integer", min_value=1, max_value=10)
        assert isinstance(rand_int, int)
        assert 1 <= rand_int <= 10
        
        # Test float generation
        rand_float = random_generator("float", min_value=0.0, max_value=1.0)
        assert isinstance(rand_float, float)
        assert 0.0 <= rand_float <= 1.0
        
        # Test string generation
        rand_string = random_generator("string", length=8, charset="letters")
        assert isinstance(rand_string, str)
        assert len(rand_string) == 8
        assert rand_string.isalpha()
        
        # Test boolean generation
        rand_bool = random_generator("boolean")
        assert isinstance(rand_bool, bool)
        
        # Test UUID generation
        rand_uuid = random_generator("uuid")
        assert isinstance(rand_uuid, str)
        assert len(rand_uuid) == 36  # Standard UUID length
    
    def test_text_processor(self):
        """Test text processing functionality."""
        assert text_processor("hello world", "uppercase") == "HELLO WORLD"
        assert text_processor("HELLO WORLD", "lowercase") == "hello world"
        assert text_processor("hello world", "title") == "Hello World"
        assert text_processor("hello", "reverse") == "olleh"
        assert text_processor("hello world", "word_count") == 2
        assert text_processor("hello", "char_count") == 5
        assert text_processor("  hello world  ", "trim") == "hello world"
    
    def test_json_formatter(self):
        """Test JSON formatting functionality."""
        test_json = '{"name":"John","age":30}'
        
        # Test formatting
        formatted = json_formatter(test_json, "format")
        assert "{\n" in formatted  # Should be pretty-printed
        
        # Test validation
        assert json_formatter(test_json, "validate") == True
        assert json_formatter('{"invalid": json}', "validate") == False
        
        # Test minification
        minified = json_formatter(test_json, "minify")
        assert " " not in minified  # Should be compact
    
    def test_json_formatter_validation(self):
        """Test JSON formatter validation."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            json_formatter('{"invalid": json}', "format")


class TestGlobalRegistry:
    """Test the global registry with actual tools."""
    
    def test_tools_registered(self):
        """Test that tools are registered in global registry."""
        # Import tools to trigger registration
        import tools.calculator
        import tools.utilities
        
        tools = registry.list_tools()
        tool_names = [tool["name"] for tool in tools]
        
        # Check that our tools are registered
        assert "calculator" in tool_names
        assert "echo" in tool_names
        assert "time" in tool_names
        assert "random_generator" in tool_names
    
    def test_tool_categories(self):
        """Test tool categorization."""
        categories = registry.list_categories()
        
        assert "math" in categories
        assert "utility" in categories
        assert "help" in categories
    
    def test_execute_registered_tools(self):
        """Test executing tools from global registry."""
        # Test calculator
        result = registry.execute_tool("calculator", {"operation": "add", "a": 5, "b": 3})
        assert result == 8
        
        # Test echo
        result = registry.execute_tool("echo", {"message": "test"})
        assert result == "test"
