/**
 * @file A very reduced subset of Java, plus restricted JML.
 * @author Alexander Gottfried <alexander.gottfried@stud.tu-darmstadt.de>
 * @license MIT
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

// ======================
// The lines below up until 'END COPYRIGHT' are adapted from tree-sitter-java
// (https://github.com/tree-sitter/tree-sitter-java) and modified for my purposes.
//
// Copyright (c) 2017 Ayman Nadeem

const DIGITS = token(choice('0', seq(/[1-9]/, optional(seq(optional('_'), sep1(/[0-9]+/, /_+/))))));

/**
 * Creates a rule to optionally match one or more of the rules separated by a comma
 *
 * @param {RuleOrLiteral} rule
 *
 * @returns {ChoiceRule}
 */
function commaSep(rule) {
  return optional(commaSep1(rule));
}

/**
 * Creates a rule to match one or more of the rules separated by a comma
 *
 * @param {RuleOrLiteral} rule
 *
 * @returns {SeqRule}
 */
function commaSep1(rule) {
  return seq(rule, repeat(seq(',', rule)));
}

/**
 * Creates a rule to match one or more of the rules separated by `separator`
 *
 * @param {RuleOrLiteral} rule
 *
 * @param {RuleOrLiteral} separator
 *
 * @returns {SeqRule}
 */
function sep1(rule, separator) {
  return seq(rule, repeat(seq(separator, rule)));
}

const PREC = {
  COMMENT: 0,         // //  /*  */
  ASSIGN: 1,          // =  += -=  *=  /=  %=  &=  ^=  |=  <<=  >>=  >>>=
  DECL: 2,
  ELEMENT_VAL: 2,
  TERNARY: 3,         // ?:
  LOGIC_EQUALITY: 4,   // <==>  <=!=>
  IMPLIES: 5,          // ==>  <==
  OR: 6,              // ||
  AND: 7,             // &&
  BIT_OR: 8,          // |
  BIT_XOR: 9,         // ^
  BIT_AND: 10,         // &
  EQUALITY: 11,        // ==  !=
  GENERIC: 12,
  REL: 13,            // <  <=  >  >=  instanceof
  SUBTYPE: 13,        // <:
  SHIFT: 14,          // <<  >>  >>>
  ADD: 15,            // +  -
  MULT: 16,           // *  /  %
  CAST: 17,           // (Type)
  OBJ_INST: 17,       // new
  UNARY: 18,          // ++a  --a  a++  a--  +  -  !  ~
  ARRAY: 19,          // [Index]
  OBJ_ACCESS: 19,     // .
  SUM: 20,            // \num_of  \product  \sum
  PARENS: 21,         // (Expression)
  CLASS_LITERAL: 21,  // .
  QUANT: 21,          // \forall  \exists  \max  \min
}

module.exports = grammar({
  word: $ => $.identifier,

  rules: {
    program: $ => repeat($._toplevel_statement),

    _toplevel_statement: $ => choice(
      $.variable_declaration,
      $.method_declaration,
      $._jml_toplevel_annotation,
    ),

    variable_declaration: $ => seq(
      field('type', $._type),
      $._variable_declaration_list,
      ';',
    ),

    _variable_declaration_list: $ => commaSep1(
      field('decl', $.variable_declaration),
    ),

    variable_declaration: $ => seq(
      $._variable_id,
      optional(seq('=', field('value', $._expression))),
    ),

    _variable_id: $ => field('name', $.identifier),

    method_declaration: $ => seq(
      $._method_header,
      field('body', $.block),
    ),

    _method_header: $ => seq(
      optional($.jml_contract),
      field('name', $.identifier),
      field('parameters', $.parameters),
    ),

    parameters: $ => seq(
      '(',
      commaSep($.parameter),
      ')',
    ),

    parameter: $ => seq(
      field('type', $._type),
      $._variable_id,
    ),

    block: $ => seq(
      '{',
      // for now, ignore method bodies
      //repeat($.statement),
      '}',
    ),

    _expression: $ => choice(
      $.binary_expression,
      $._primary_expression,
    ),

    binary_expression: $ => choice(
      ...[
        ['>', PREC.REL],
        ['<', PREC.REL],
        ['>=', PREC.REL],
        ['<=', PREC.REL],
        ['==', PREC.EQUALITY],
        ['!=', PREC.EQUALITY],
        ['&&', PREC.AND],
        ['||', PREC.OR],
        ['+', PREC.ADD],
        ['-', PREC.ADD],
        ['*', PREC.MULT],
        ['/', PREC.MULT],
        ['&', PREC.BIT_AND],
        ['|', PREC.BIT_OR],
        ['^', PREC.BIT_XOR],
        ['%', PREC.MULT],
        ['<<', PREC.SHIFT],
        ['>>', PREC.SHIFT],
        ['>>>', PREC.SHIFT],
        ['==>', PREC.IMPLIES],
        ['<==', PREC.IMPLIES],
        ['<==>', PREC.LOGIC_EQUALITY],
        ['<=!=>', PREC.LOGIC_EQUALITY],
        // we leave out <: for now
      ].map(([operator, precedence]) =>
        prec.left(precedence, seq(
          field('left', $._expression),
          // @ts-ignore
          field('operator', operator),
          field('right', $._expression),
        )),
      )),
    // we also leave out quantifiers for now

    _primary_expression: $ => choice(
      $._literal,
      $.identifier,
      $.jml_old,
    ),

    _literal: $ => choice(
      $.decimal_integer_literal,
      $.true,
      $.false,
    ),

    decimal_integer_literal: _ => token(seq(
      DIGITS,
      optional(choice('l', 'L')),
    )),

    true: _ => 'true',
    false: _ => 'false',

    identifier: _ => /[\p{XID_Start}_$][\p{XID_Continue}\u00A2_$]*/,

    _type: $ => choice(
      $.integral_type,
      $.boolean_type,
    ),

    integral_type: _ => 'int',
    boolean_type: _ => 'boolean',

    // END COPYRIGHT
    // =============

    jml_set_statement: $ => seq(
      '//@',
      'set',
      $.variable_declaration,
      ';',
    ),

    jml_contract: $ => repeat1(seq(
      '//@',
      $._jml_clause,
      ';',
    )),

    _jml_clause: $ => choice(
      $.jml_requires,
      $.jml_ensures,
    ),

    jml_requires: $ => seq(
      choice('requires', 'pre'),
      $._expression,
    ),

    jml_ensures: $ => seq(
      choice('ensures', 'post'),
      $._expression,
    ),


    _jml_toplevel_annotation: $ => seq(
      '//@',
      choice(
        $.jml_invariant,
        $.jml_ghost_declaration,
      ),
      ';',
    ),

    jml_invariant: $ => seq(
      'invariant',
      $._expression,
    ),

    jml_ghost_declaration: $ => seq(
      'ghost',
			optional(field('final', 'final')),
      field('type', $._type),
      $.variable_declaration,
    ),

    jml_old: $ => seq(
      '\\old(',
      $.identifier,
      ')',
    ),
  },

  name: "java_jml_subset",
});
