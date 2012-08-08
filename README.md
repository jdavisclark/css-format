# css-format
This is a general purpose css formatting library, originally ported from the javascript formatter over at [the js-beautifier project](/einars/js-beautify/blob/master/beautify-css.js).
css-format supports all the features of the original js-beautifer library, plus a bunch more (with more to come).


### Options
* **indent_string**: string to use for each indentation. defaults to **\t**
* **indent_size**: number of indent strings to use for each indentation. defaults to **1**
* **newline**: the newline character. defaults to **\n**
* **end_with_newline**: end the file with a blank line. defaults to **False**
* **comment_line_max**: maximum number of characters in a comment line. comments longer than comment_line_max will be word-wrapped to new lines. newlines in the original comment are replaced with spaces prior to formatting. defaults to **100**
* **blank_line_above_comments**: always prefix comments with a blank line. defaults to **True**
* **indent_comment_body**: indents multiline comments by indent_string\*indent_size. defaults to **True**
* **one_line_comments_under_max**: put comments under the maximum character limit all on one line, rather than putting the begin/end comment delimiters on their own lines. defaults to **True**
* **close_input**: close the input file/stream after formatting, if applicable. defaults to **True**
* **close_output**: close the output file/stream after formatting. defaults to **False**


### Usage

*you have potentially ugly css in a string, you want it to be awesome, you care about literally nothing else*:
```python
from cssformat import format_css

css = "/* make input elements more awesome */ input:hover{background-color: red;}"
css = format_css(css)
```



*format some css in a string, indent with 2 spaces, end with newline*:
```python
from cssformat import format_css, CssFormatOptions

css = "/* make input elements more awesome */ input:hover{background-color: red;}"
opts = CssFormatOptions()
opts.end_with_newline = True
opts.indent_string = " "
opts.indent_size = 2

# note: the format_css helper function ignores non-default values for close_input and close_ouput, for obvious reasons
css = format_css(css, opts=opts)
```



*Read from a css file, write formatted css to another file, default options:*
```python
import io
from cssformat import CssFormatter

finput = open("./mycss.css", "r")
foutput = open("./sweet_code.css", "w")
formatter = CssFormatter(finput, foutput)
formatter.format()
foutput.close() # the call to format has already called flush, and fsync if applicable
```

*(alternate) Format some css stored in a string, turn off comment indention and single line comments, write output to a StringIO stream:*
```python
from StringIO import StringIO
from cssformat import CssFormatter, CssFormatOptions

my_css = "/*make text inputs beautiful*/ input[type=text]{color: green;background-color: red;}"
opts = CssFormatOptions()
opts.indent_comment_body=False
opts.one_line_comments_under_max=False
soutput = StringIO()

formatter = CssFormatter(my_css, soutput, opts=opts)
formatter.format()
sweet_code = soutput.getvalue()
soutput.close()
```

### Why isn't everything in one big file?
Becuase everything in scanner.py is generic and can be re-used. Feel free to throw the contents of scanner.py in to cssformat.py and delete `from scanner import Scanner` before you use it. I may add a pre-commit hook to do this automatically in the future.