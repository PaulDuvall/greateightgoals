# Code Refactoring Recommendations

This document identifies refactoring opportunities in the Ovechkin Goal Tracker codebase based on Martin Fowler's *Refactoring* catalog. Each recommendation includes the specific refactoring pattern, location, rationale, and severity level.

## Refactorings Grouped by Type

## Refactoring: Extract Function
🔗 Reference: https://refactoring.com/catalog/extractFunction.html

- **File**: `ovechkin_tracker/ovechkin_data.py`
  - **Function**: `_fetch_and_calculate_stats`
  - **LOC**: 87-179
  - **Severity**: High
  - **Reason**: Long Method smell - this method performs multiple distinct operations (fetching data, calculating stats, finding record game, building dictionaries)
  - **Recommendation**: Split into smaller focused functions, each handling a single responsibility

- **File**: `ovechkin_tracker/nhl_api.py`
  - **Function**: `get_remaining_games`
  - **LOC**: 113-187
  - **Severity**: Medium
  - **Reason**: Long Method smell - combines API request, data parsing, date formatting, and game filtering
  - **Recommendation**: Extract separate functions for date formatting and game data transformation

- **File**: `aws-static-website/update_website.py`
  - **Function**: `generate_html_content`
  - **LOC**: 21-724
  - **Severity**: High
  - **Reason**: Very Long Method smell - contains extensive HTML generation and date formatting logic
  - **Recommendation**: Extract template rendering into separate functions or use a template engine

- **File**: `ovechkin_tracker/email.py`
  - **Function**: `format_email_html`
  - **LOC**: 167-256
  - **Severity**: Medium
  - **Reason**: Long Method smell - mixes HTML template generation with data extraction
  - **Recommendation**: Extract HTML template to a separate file or function

## Refactoring: Replace Magic Number with Symbolic Constant
🔗 Reference: https://refactoring.com/catalog/replaceMagicLiteral.html

- **File**: `ovechkin_tracker/ovechkin_data.py`
  - **Function**: `_fetch_and_calculate_stats`
  - **LOC**: 116
  - **Severity**: Medium
  - **Reason**: Magic Number smell - hard-coded value `82` for total season games
  - **Recommendation**: Define as a named constant at the class or module level

- **File**: `ovechkin_tracker/email.py`
  - **Function**: `format_email_html`
  - **LOC**: 196
  - **Severity**: Medium
  - **Reason**: Magic Number smell - hard-coded value `894` for Gretzky's record
  - **Recommendation**: Import the constant from OvechkinData class

## Refactoring: Extract Class
🔗 Reference: https://refactoring.com/catalog/extractClass.html

- **File**: `ovechkin_tracker/nhl_api.py`
  - **Module Level**
  - **LOC**: 1-198
  - **Severity**: Medium
  - **Reason**: Large Class smell - module contains multiple responsibilities (API requests, data formatting, caching)
  - **Recommendation**: Extract an `NHLApiClient` class to encapsulate API interaction

- **File**: `aws-static-website/update_website.py`
  - **Function**: `generate_html_content`
  - **LOC**: 21-724
  - **Severity**: High
  - **Reason**: Large Class smell - function contains extensive HTML template logic
  - **Recommendation**: Extract a `TemplateRenderer` class to handle HTML generation

## Refactoring: Replace Conditional with Polymorphism
🔗 Reference: https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html

- **File**: `ovechkin_tracker/nhl_api.py`
  - **Function**: `get_remaining_games`
  - **LOC**: 131-183
  - **Severity**: Medium
  - **Reason**: Conditional Complexity smell - complex conditional logic for parsing different API responses
  - **Recommendation**: Create strategy classes for different API response formats

## Refactoring: Introduce Parameter Object
🔗 Reference: https://refactoring.com/catalog/introduceParameterObject.html

- **File**: `ovechkin_tracker/ovechkin_data.py`
  - **Function**: `_find_and_set_record_game`
  - **LOC**: 202-285
  - **Severity**: Low
  - **Reason**: Data Clumps smell - date-related variables are passed and manipulated together
  - **Recommendation**: Create a `GameDate` class to encapsulate date formatting operations

## Refactoring: Move Function
🔗 Reference: https://refactoring.com/catalog/moveFunction.html

- **File**: `ovechkin_tracker/ovechkin_data.py`
  - **Function**: `enable_debug_logging`
  - **LOC**: 23-35
  - **Severity**: Low
  - **Reason**: Feature Envy smell - function doesn't use any class data but is in the module
  - **Recommendation**: Move to a separate logging utility module

## Refactoring: Encapsulate Variable
🔗 Reference: https://refactoring.com/catalog/encapsulateVariable.html

- **File**: `ovechkin_tracker/nhl_api.py`
  - **Module Level**
  - **LOC**: 19-22
  - **Severity**: Medium
  - **Reason**: Global Data smell - module-level constants are directly accessed
  - **Recommendation**: Encapsulate in a configuration class with getter methods

## Refactoring: Extract Variable
🔗 Reference: https://refactoring.com/catalog/extractVariable.html

- **File**: `ovechkin_tracker/nhl_api.py`
  - **Function**: `get_remaining_games`
  - **LOC**: 169-175
  - **Severity**: Low
  - **Reason**: Long Expression smell - complex expressions for determining opponent team
  - **Recommendation**: Extract intermediate variables with meaningful names

## Refactoring: Split Phase
🔗 Reference: https://refactoring.com/catalog/splitPhase.html

- **File**: `ovechkin_tracker/ovechkin_data.py`
  - **Function**: `_fetch_and_calculate_stats`
  - **LOC**: 87-179
  - **Severity**: Medium
  - **Reason**: Divergent Change smell - method handles both data fetching and calculation
  - **Recommendation**: Split into separate phases for data retrieval and calculation

## Refactoring: Replace Temp with Query
🔗 Reference: https://refactoring.com/catalog/replaceTempWithQuery.html

- **File**: `ovechkin_tracker/ovechkin_data.py`
  - **Function**: `_fetch_and_calculate_stats`
  - **LOC**: 129-131
  - **Severity**: Low
  - **Reason**: Temporary Variable smell - calculation results stored in temporary variables
  - **Recommendation**: Replace with query methods that compute these values

## Refactoring: Inline Function
🔗 Reference: https://refactoring.com/catalog/inlineFunction.html

- **File**: `ovechkin_tracker/nhl_api.py`
  - **Function**: `_make_api_request`
  - **LOC**: 33-70
  - **Severity**: Low
  - **Reason**: Middle Man smell - function adds little value beyond the requests library
  - **Recommendation**: Consider inlining for simple cases or enhancing with more robust features

## Refactoring: Consolidate Conditional Expression
🔗 Reference: https://refactoring.com/catalog/consolidateConditionalExpression.html

- **File**: `aws-static-website/update_website.py`
  - **Function**: `generate_html_content`
  - **LOC**: 50-90
  - **Severity**: Medium
  - **Reason**: Complicated Conditional smell - multiple nested conditions for date formatting
  - **Recommendation**: Consolidate related conditions and extract to helper methods

---

## Refactorings Grouped by Severity

## Severity: High

- **Refactoring**: Extract Function  
  🔗 https://refactoring.com/catalog/extractFunction.html  
  - **File**: `ovechkin_tracker/ovechkin_data.py`
  - **Function**: `_fetch_and_calculate_stats`
  - **LOC**: 87-179
  - **Reason**: Long Method smell - this method performs multiple distinct operations (fetching data, calculating stats, finding record game, building dictionaries)
  - **Recommendation**: Split into smaller focused functions, each handling a single responsibility

- **Refactoring**: Extract Function  
  🔗 https://refactoring.com/catalog/extractFunction.html  
  - **File**: `aws-static-website/update_website.py`
  - **Function**: `generate_html_content`
  - **LOC**: 21-724
  - **Reason**: Very Long Method smell - contains extensive HTML generation and date formatting logic
  - **Recommendation**: Extract template rendering into separate functions or use a template engine

- **Refactoring**: Extract Class  
  🔗 https://refactoring.com/catalog/extractClass.html  
  - **File**: `aws-static-website/update_website.py`
  - **Function**: `generate_html_content`
  - **LOC**: 21-724
  - **Reason**: Large Class smell - function contains extensive HTML template logic
  - **Recommendation**: Extract a `TemplateRenderer` class to handle HTML generation

## Severity: Medium

- **Refactoring**: Extract Function  
  🔗 https://refactoring.com/catalog/extractFunction.html  
  - **File**: `ovechkin_tracker/nhl_api.py`
  - **Function**: `get_remaining_games`
  - **LOC**: 113-187
  - **Reason**: Long Method smell - combines API request, data parsing, date formatting, and game filtering
  - **Recommendation**: Extract separate functions for date formatting and game data transformation

- **Refactoring**: Extract Function  
  🔗 https://refactoring.com/catalog/extractFunction.html  
  - **File**: `ovechkin_tracker/email.py`
  - **Function**: `format_email_html`
  - **LOC**: 167-256
  - **Reason**: Long Method smell - mixes HTML template generation with data extraction
  - **Recommendation**: Extract HTML template to a separate file or function

- **Refactoring**: Replace Magic Number with Symbolic Constant  
  🔗 https://refactoring.com/catalog/replaceMagicLiteral.html  
  - **File**: `ovechkin_tracker/ovechkin_data.py`
  - **Function**: `_fetch_and_calculate_stats`
  - **LOC**: 116
  - **Reason**: Magic Number smell - hard-coded value `82` for total season games
  - **Recommendation**: Define as a named constant at the class or module level

- **Refactoring**: Replace Magic Number with Symbolic Constant  
  🔗 https://refactoring.com/catalog/replaceMagicLiteral.html  
  - **File**: `ovechkin_tracker/email.py`
  - **Function**: `format_email_html`
  - **LOC**: 196
  - **Reason**: Magic Number smell - hard-coded value `894` for Gretzky's record
  - **Recommendation**: Import the constant from OvechkinData class

- **Refactoring**: Extract Class  
  🔗 https://refactoring.com/catalog/extractClass.html  
  - **File**: `ovechkin_tracker/nhl_api.py`
  - **Module Level**
  - **LOC**: 1-198
  - **Reason**: Large Class smell - module contains multiple responsibilities (API requests, data formatting, caching)
  - **Recommendation**: Extract an `NHLApiClient` class to encapsulate API interaction

- **Refactoring**: Replace Conditional with Polymorphism  
  🔗 https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html  
  - **File**: `ovechkin_tracker/nhl_api.py`
  - **Function**: `get_remaining_games`
  - **LOC**: 131-183
  - **Reason**: Conditional Complexity smell - complex conditional logic for parsing different API responses
  - **Recommendation**: Create strategy classes for different API response formats

- **Refactoring**: Encapsulate Variable  
  🔗 https://refactoring.com/catalog/encapsulateVariable.html  
  - **File**: `ovechkin_tracker/nhl_api.py`
  - **Module Level**
  - **LOC**: 19-22
  - **Reason**: Global Data smell - module-level constants are directly accessed
  - **Recommendation**: Encapsulate in a configuration class with getter methods

- **Refactoring**: Split Phase  
  🔗 https://refactoring.com/catalog/splitPhase.html  
  - **File**: `ovechkin_tracker/ovechkin_data.py`
  - **Function**: `_fetch_and_calculate_stats`
  - **LOC**: 87-179
  - **Reason**: Divergent Change smell - method handles both data fetching and calculation
  - **Recommendation**: Split into separate phases for data retrieval and calculation

- **Refactoring**: Consolidate Conditional Expression  
  🔗 https://refactoring.com/catalog/consolidateConditionalExpression.html  
  - **File**: `aws-static-website/update_website.py`
  - **Function**: `generate_html_content`
  - **LOC**: 50-90
  - **Reason**: Complicated Conditional smell - multiple nested conditions for date formatting
  - **Recommendation**: Consolidate related conditions and extract to helper methods

## Severity: Low

- **Refactoring**: Introduce Parameter Object  
  🔗 https://refactoring.com/catalog/introduceParameterObject.html  
  - **File**: `ovechkin_tracker/ovechkin_data.py`
  - **Function**: `_find_and_set_record_game`
  - **LOC**: 202-285
  - **Reason**: Data Clumps smell - date-related variables are passed and manipulated together
  - **Recommendation**: Create a `GameDate` class to encapsulate date formatting operations

- **Refactoring**: Move Function  
  🔗 https://refactoring.com/catalog/moveFunction.html  
  - **File**: `ovechkin_tracker/ovechkin_data.py`
  - **Function**: `enable_debug_logging`
  - **LOC**: 23-35
  - **Reason**: Feature Envy smell - function doesn't use any class data but is in the module
  - **Recommendation**: Move to a separate logging utility module

- **Refactoring**: Extract Variable  
  🔗 https://refactoring.com/catalog/extractVariable.html  
  - **File**: `ovechkin_tracker/nhl_api.py`
  - **Function**: `get_remaining_games`
  - **LOC**: 169-175
  - **Reason**: Long Expression smell - complex expressions for determining opponent team
  - **Recommendation**: Extract intermediate variables with meaningful names

- **Refactoring**: Replace Temp with Query  
  🔗 https://refactoring.com/catalog/replaceTempWithQuery.html  
  - **File**: `ovechkin_tracker/ovechkin_data.py`
  - **Function**: `_fetch_and_calculate_stats`
  - **LOC**: 129-131
  - **Reason**: Temporary Variable smell - calculation results stored in temporary variables
  - **Recommendation**: Replace with query methods that compute these values

- **Refactoring**: Inline Function  
  🔗 https://refactoring.com/catalog/inlineFunction.html  
  - **File**: `ovechkin_tracker/nhl_api.py`
  - **Function**: `_make_api_request`
  - **LOC**: 33-70
  - **Reason**: Middle Man smell - function adds little value beyond the requests library
  - **Recommendation**: Consider inlining for simple cases or enhancing with more robust features
