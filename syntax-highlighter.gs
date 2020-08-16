// Syntax highlighter for LaTeX syntax in Google Docs.
// See README.md for installation and usage instructions.
// original author: Krzysztof Gajos
// contributors: Kapil Garg
// Last Updated: September 11, 2019

/**
 * The onOpen function runs automatically when the Google Docs document is
 * opened. Use it to add custom menus to Google Docs that allow the user to run
 * custom scripts. For more information, please consult the following two
 * resources.
 *
 * Extending Google Docs developer guide:
 *     https://developers.google.com/apps-script/guides/docs
 *
 * Document service reference documentation:
 *     https://developers.google.com/apps-script/reference/document/
 */
function onOpen() {
  // Add a menu with some items, some separators, and a sub-menu.
  DocumentApp.getUi().createMenu('Syntax highlighting')
      .addItem('Highlight LaTeX syntax', 'highlightSyntax')
      .addToUi();
}


function highlightSyntax() {
  var body = DocumentApp.getActiveDocument().getBody();

  // reset formatting
  var bodyAsText = body.editAsText();
//  bodyAsText.setBold(false);
//  bodyAsText.setItalic(false);
//  bodyAsText.setForegroundColor("#000000");
//  bodyAsText.setBackgroundColor("#FFFFFF");
  // TODO still need to figure out how to reset all paragraphs to normal text

  // highlight tags
  var tagRegExp = "\\\\[a-zA-Z]+";
  var tagColor = "#AA0000";
  syntaxHighlightHelper(tagRegExp, function(text, startOffset, endOffset) {text.setForegroundColor(startOffset, endOffset, tagColor);});

  // bold
  syntaxHighlightHelper("\\\\bf[^}]+}", function(text, startOffset, endOffset) {text.setBold(startOffset +3, endOffset - 1, true);});
  syntaxHighlightHelper("\\\\textbf{[^}]+}", function(text, startOffset, endOffset) {text.setBold(startOffset +8, endOffset - 1, true);});

  // italics
  syntaxHighlightHelper("\\\\it[\\s\\\\][^}]+}", function(text, startOffset, endOffset) {text.setItalic(startOffset +3, endOffset - 1, true);});
  syntaxHighlightHelper("\\\\textit{[^}]+}", function(text, startOffset, endOffset) {text.setItalic(startOffset +8, endOffset - 1, true);});

  // emph
  syntaxHighlightHelper("\\\\emph{[^}]+}", function(text, startOffset, endOffset) {text.setItalic(startOffset +6, endOffset - 1, true);});
  syntaxHighlightHelper("\\\\em[^}]+}", function(text, startOffset, endOffset) {text.setItalic(startOffset +3, endOffset - 1, true);});

  // set format for sections and subsections
  syntaxHighlightHelper("\\\\title{[^}]+}", function(text, startOffset, endOffset) {text.getParent().asParagraph().setHeading(DocumentApp.ParagraphHeading.TITLE).setIndentFirstLine(0);});
  syntaxHighlightHelper("\\\\chapter{[^}]+}", function(text, startOffset, endOffset) {text.getParent().asParagraph().setHeading(DocumentApp.ParagraphHeading.HEADING1).setIndentFirstLine(0);});
  syntaxHighlightHelper("\\\\section{[^}]+}", function(text, startOffset, endOffset) {text.getParent().asParagraph().setHeading(DocumentApp.ParagraphHeading.HEADING2).setIndentFirstLine(0);});
  syntaxHighlightHelper("\\\\subsection{[^}]+}", function(text, startOffset, endOffset) {text.getParent().asParagraph().setHeading(DocumentApp.ParagraphHeading.HEADING3).setIndentFirstLine(0);});
  syntaxHighlightHelper("\\\\subsubsection{[^}]+}", function(text, startOffset, endOffset) {text.getParent().asParagraph().setHeading(DocumentApp.ParagraphHeading.HEADING4).setIndentFirstLine(0);});

  // highlight comments that start at the beginning of a line
  var commentRegExp = "^%.+$";
  var commentColor = "#888888";
  syntaxHighlightHelper(commentRegExp, function(text, startOffset, endOffset) {text.setForegroundColor(startOffset, endOffset, commentColor);});

  // highlight comments that start in the middle of a line
  var commentRegExp = "[^\\\\]%.+$";
  var commentColor = "#888888";
  syntaxHighlightHelper(commentRegExp, function(text, startOffset, endOffset) {text.setForegroundColor(startOffset+1, endOffset, commentColor);});

//  // highlight block comments starting with \if and ending with \fi
//  var commentRegExp =   "(\\\\if)([\\S\\s]*?)(\\\\fi)";
//  var commentRegExp = "(\\\\if)(\\s*)([\\S\\s]*?)(\\s*)(\\\\fi)";
//  var commentColor = "#888888";
//  highlightBlockComments(function(text, startOffset, endOffset) {text.setForegroundColor(startOffset, endOffset, commentColor);});
//  syntaxHighlightHelper(commentRegExp, function(text, startOffset, endOffset) {text.setForegroundColor(startOffset + 5, endOffset - 3, commentColor);});
}

function syntaxHighlightHelper(regexp, formattingFunction) {
  var body = DocumentApp.getActiveDocument().getBody();

  var selection = body.findText("% LATEX FORMATTING CODE START %");
  if (selection) {
    selection = body.findText(regexp, selection);
  }
  else {
    selection = body.findText(regexp);
  }


  while (selection) {
    var text = selection.getElement().editAsText();
    Logger.log(text.getText());
    formattingFunction(text, selection.getStartOffset(), selection.getEndOffsetInclusive());
    selection = body.findText(regexp, selection);
  }
}

//function highlightBlockComments(formattingFunction) {
//  var body = DocumentApp.getActiveDocument().getBody();
//  var selectionStart = body.findText("BEGIN_DOCUMENT");
//  var selectionEnd;
//
//  if (selectionStart) {
//    selectionStart = body.findText(regexp, selectionStart);
//  }
//  else {
//    selectionStart = body.findText("\\\\if");
//    selectionEnd = body.findText("\\\\fi");
//  }
//
//
//  while (selectionStart) {
//    if (selectionEnd) {
//     Logger.log(selectionStart.getElement().editAsText().getText());
//
//      // get start offset
//      var startOffset = selectionStart.getEndOffsetInclusive();
//      var endOffset = selectionEnd.getStartOffset();
//
//      Logger.log(startOffset);
//      Logger.log(endOffset);
//
//      var text = selectionStart.getElement().editAsText();
//      formattingFunction(text, startOffset, endOffset);
//
//      selectionStart = body.findText("\\\\if", selectionEnd);
//      selectionEnd = body.findText("\\\\fi", selectionEnd);
//    }
//  }
//}