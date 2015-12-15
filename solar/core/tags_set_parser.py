#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import re

from ply import lex
from ply import yacc

from solar import errors


tokens = (
    "STRING",
    "AND",
    "OR",
    "LPAREN",
    "RPAREN",
    "ANY",
    "EQ")

t_STRING = r'[A-Za-z0-9-_/\\]+'
t_EQ = r'='
t_ANY = r'\*'
t_AND = '&|,'
t_OR = r'\|'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_ignore = ' \t\r\n'


class SubexpressionWrapper(object):

    def __init__(self, subexpression):
        self.subexpression = subexpression

    def evaluate(self):
        self.value = self.subexpression()
        return self.value

    def __call__(self):
        self.evaluate()
        return self.value


class ScalarWrapper(object):

    def __init__(self, value):
        global expression
        self.value = (set([value]) <= set(expression.tags))

    def evaluate(self):
        return self.value

    def __call__(self):
        return self.value


class AnyWrapper(object):

    def __init__(self, value):
        global expression
        # convert all tags from key=value to key=*
        tags = map(lambda s: re.sub('=\w+', '=*', s), expression.tags)
        self.value = (set([value]) <= set(tags))

    def evaluate(self):
        return self.value

    def __call__(self):
        return self.value


def p_expression_logical_op(p):
    """expression : expression AND expression
                  | expression OR expression
    """
    result, arg1, op, arg2 = p
    if op == '&' or op == ',':
        result = lambda: arg1() and arg2()
    elif op == '|':
        result = lambda: arg1() or arg2()

    p[0] = SubexpressionWrapper(result)


def p_expression_string(p):
    """expression : STRING"""
    p[0] = ScalarWrapper(p[1] + '=')


def p_expression_assign(p):
    """expression : STRING EQ STRING
                  | STRING EQ
    """
    if len(p) == 3:
        last = ''
    else:
        last = p[3]
    p[0] = ScalarWrapper(p[1] + p[2] + last)


def p_expression_assign_any(p):
    """expression : STRING EQ ANY"""
    p[0] = AnyWrapper(p[1] + p[2] + p[3])


def p_expression_group(p):
    """xpression : LPAREN expression RPAREN"""
    p[0] = p[2]


def t_error(t):
    errors.LexError("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


def p_error(p):
    raise errors.ParseError(
        "Syntax error at '{0}'".format(getattr(p, 'value', '')))


class Expression(object):

    def __init__(self, expression_text, tags):
        self.expression_text = expression_text
        self.tags = tags
        self.compiled_expression = parse(self)

    def evaluate(self):
        return self.compiled_expression()


lexer = lex.lex()
parser = yacc.yacc(debug=False, write_tables=False, errorlog=yacc.NullLogger())
expression = None


def get_string_tokens(txt):
    lexer.input(txt)
    parsed = []
    token_part = ''
    for token in lexer:
        if token.type in ['STRING', 'ANY', 'EQ']:
            token_part += token.value
        else:
            if token_part:
                parsed.append(token_part)
                token_part = ''
    if token_part:
        parsed.append(token_part)
    return parsed


def parse(expr):
    global parser
    global expression
    # TODO it's very very bad to have global variable here
    # we should figure a way to pass it into ScalarWrapper
    expression = expr
    return parser.parse(expr.expression_text)
