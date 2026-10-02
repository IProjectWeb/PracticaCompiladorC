"""Pruebas del analizador léxico de Mini C según la especificación de Kirks Fans."""

from minic.diagnostics.diagnostic import Diagnostic
from minic.lexer.lexer import Lexer
from minic.lexer.token import Token
from minic.lexer.token_type import TokenType
from minic.output.diagnostic_printer import format_diagnostic
from minic.output.token_printer import format_token


def test_section_7_case_1() -> None:
    source = "int2 = 12abc;\nwhilex == -5"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []

    formatted_tokens = [format_token(t) for t in tokens]
    expected_tokens = [
        "IDENTIFIER 'int2' 1 1",
        "ASSIGN '=' 1 6",
        "INTEGER_LITERAL '12' 1 8",
        "IDENTIFIER 'abc' 1 10",
        "SEMICOLON ';' 1 13",
        "IDENTIFIER 'whilex' 2 1",
        "EQUAL_EQUAL '==' 2 8",
        "MINUS '-' 2 11",
        "INTEGER_LITERAL '5' 2 12",
        "EOF '' 2 13",
    ]
    assert formatted_tokens == expected_tokens

    # Verificar literales enteros
    assert tokens[2].literal == 12
    assert tokens[8].literal == 5
    for idx in (0, 1, 3, 4, 5, 6, 7, 9):
        assert tokens[idx].literal is None


def test_section_7_case_2_with_errors() -> None:
    source = "int x = @;\nx ! = 0; // fin"
    tokens, diagnostics = Lexer(source).scan()

    formatted_tokens = [format_token(t) for t in tokens]
    expected_tokens = [
        "KW_INT 'int' 1 1",
        "IDENTIFIER 'x' 1 5",
        "ASSIGN '=' 1 7",
        "SEMICOLON ';' 1 10",
        "IDENTIFIER 'x' 2 1",
        "ASSIGN '=' 2 5",
        "INTEGER_LITERAL '0' 2 7",
        "SEMICOLON ';' 2 8",
        "IDENTIFIER 'fin' 2 13",
        "EOF '' 2 16",
    ]
    assert formatted_tokens == expected_tokens

    formatted_diagnostics = [format_diagnostic(d) for d in diagnostics]
    expected_diagnostics = [
        "LEX001 error 1:9 Carácter no reconocido: '@'",
        "LEX001 error 2:3 Carácter no reconocido: '!'",
        "LEX001 error 2:10 Carácter no reconocido: '/'",
        "LEX001 error 2:11 Carácter no reconocido: '/'",
    ]
    assert formatted_diagnostics == expected_diagnostics


def test_all_15_tokens() -> None:
    source = "int while x 123 = == != + - ( ) { } ;"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []
    types = [t.type for t in tokens]
    expected_types = [
        TokenType.KW_INT,
        TokenType.KW_WHILE,
        TokenType.IDENTIFIER,
        TokenType.INTEGER_LITERAL,
        TokenType.ASSIGN,
        TokenType.EQUAL_EQUAL,
        TokenType.NOT_EQUAL,
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]
    assert types == expected_types
    assert len(tokens) == 15


def test_empty_source() -> None:
    tokens, diagnostics = Lexer("").scan()
    assert diagnostics == []
    assert len(tokens) == 1
    assert tokens[0] == Token(TokenType.EOF, "", None, 1, 1)


def test_whitespace_and_tabs_positions() -> None:
    # Tabulación (\t) cuenta como 1 columna
    # \r suelto es blanco, consume 1 columna sin nueva línea
    source = "\t \r\n  x"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []
    assert len(tokens) == 2
    # Línea 1: '\t' (col 1), ' ' (col 2), '\r' (col 3), '\n' (col 4 -> línea 2, col 1)
    # Línea 2: ' ' (col 1), ' ' (col 2), 'x' (col 3)
    assert tokens[0] == Token(TokenType.IDENTIFIER, "x", None, 2, 3)
    assert tokens[1] == Token(TokenType.EOF, "", None, 2, 4)


def test_integer_literal_values() -> None:
    source = "0 007 42"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []
    assert [t.literal for t in tokens[:-1]] == [0, 7, 42]
    assert [t.lexeme for t in tokens[:-1]] == ["0", "007", "42"]


def test_priority_keywords_over_identifier() -> None:
    source = "int while int_var while1"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []
    assert tokens[0].type == TokenType.KW_INT
    assert tokens[1].type == TokenType.KW_WHILE
    assert tokens[2].type == TokenType.IDENTIFIER
    assert tokens[3].type == TokenType.IDENTIFIER


def test_priority_double_operators_over_single() -> None:
    source = "== = != !"
    tokens, diagnostics = Lexer(source).scan()

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "LEX001"
    assert diagnostics[0].line == 1
    assert diagnostics[0].column == 9

    assert [t.type for t in tokens] == [
        TokenType.EQUAL_EQUAL,
        TokenType.ASSIGN,
        TokenType.NOT_EQUAL,
        TokenType.EOF,
    ]


def test_number_followed_by_identifier_splits() -> None:
    source = "12abc"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []
    assert tokens[0] == Token(TokenType.INTEGER_LITERAL, "12", 12, 1, 1)
    assert tokens[1] == Token(TokenType.IDENTIFIER, "abc", None, 1, 3)
    assert tokens[2] == Token(TokenType.EOF, "", None, 1, 6)


def test_negative_number_separation() -> None:
    source = "-5"
    tokens, diagnostics = Lexer(source).scan()

    assert diagnostics == []
    assert tokens[0] == Token(TokenType.MINUS, "-", None, 1, 1)
    assert tokens[1] == Token(TokenType.INTEGER_LITERAL, "5", 5, 1, 2)
    assert tokens[2] == Token(TokenType.EOF, "", None, 1, 3)


def test_diagnostics_do_not_halt_scan() -> None:
    source = "# int $ x = 1;"
    tokens, diagnostics = Lexer(source).scan()

    assert len(diagnostics) == 2
    assert diagnostics[0] == Diagnostic("LEX001", "error", "Carácter no reconocido: '#'", 1, 1)
    assert diagnostics[1] == Diagnostic("LEX001", "error", "Carácter no reconocido: '$'", 1, 7)

    types = [t.type for t in tokens]
    assert types == [
        TokenType.KW_INT,
        TokenType.IDENTIFIER,
        TokenType.ASSIGN,
        TokenType.INTEGER_LITERAL,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]
