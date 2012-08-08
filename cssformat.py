import re
from StringIO import StringIO
from scanner import Scanner

class CssFormatOptions(object):
	"""css formatting options"""
	def __init__(self):
		super(CssFormatOptions, self).__init__()

		# basic formatting
		self.indent_string = "\t"
		self.indent_size = 1
		self.newline = "\n"
		self.no_space_after = ["["]
		self.end_with_newline=False

		# comment formatting
		self.comment_line_max = 100
		self.blank_line_above_comments=True
		self.indent_comment_body=True
		self.one_line_comments_under_max=True

		# misc
		self.close_input=True
		self.close_output=False


# Forked from: http://www.python-forum.org/pythonforum/viewtopic.php?f=2&t=24947
def word_wrap(string, width=80, pre_first=0, pre_middle=0, prefix='', separators=[" "], keep_separators=False, trim=True, newline="\n"):
    """ word wrapping function.
        string: the string to wrap
        width: the column number to wrap at
        prefix: prefix each line with this string
        pre_first: prefix the first line with this number of prefixes
        pre_middle: prefix other lines with this number of prefixes
        separators: token delimiters for safe line termination
        keep_separators: keep separators at line termination
        trim: rstrip each line
    """
    string = (prefix * pre_first) + string
    newstring = ""
    
    while len(string) > width:
        # find position of nearest whitespace char to the left of "width"
        marker = width - 1
        while not string[marker] in separators:
            marker = marker - 1

        # remove line from original string and add it to the new string
        newline = string[0:marker] + (string[marker] if keep_separators else "") +newline
        newstring = newstring + newline
        hold = (prefix * pre_middle)+ string[marker + 1:]
        string = prefix + (hold.lstrip() if trim else hold)

    return newstring + string

def format_css(css, opts=CssFormatOptions()):
    # dont care if you specified values other than these, we are using the defaults
	opts.close_input = True
	opts.close_output = False

	sout = StringIO()
	formatter = CssFormatter(css, sout, opts)
	formatter.format()
	sweet_code = sout.getvalue()
	sout.close()

	return sweet_code

class CssFormatter(Scanner):
	"""css formatter"""
	def __init__(self, source, output_stream, opts=CssFormatOptions()):
		super(CssFormatter, self).__init__(source, output_stream)

		self.opts = opts
		self.re_start_comment = r"^/[*\s]+"
		self.re_end_comment = r"[\s*]+/$"
		self.re_newline = re.compile(self.opts.newline)
		self.indent_level = 0

	def indent(self):
		self.indent_level = self.indent_level + 1

	def outdent(self):
		self.indent_level = self.indent_level - 1

	def get_base_indent_string(self):
		return self.opts.indent_string * self.opts.indent_size

	def get_indent_string(self):
		return self.get_base_indent_string() * self.indent_level

	def get_newline(self):
		return self.opts.newline + self.get_indent_string()

	def write_newline(self, keep_ws=True):
		# truncate to just after the last non-whitespace char if requested
		if(not keep_ws):
			self.clear_trailing_whitespace()

		self.write(self.get_newline())

	def eat_comment(self):
		comment = StringIO()

		# add current '/' to the comment
		comment.write(self.ch())

		while(self.can_read() and self.read() != None):
			comment.write(self.ch())
			if(self.ch() == "*" and self.input_stream.peek() == "/"): # end of comment
				self.read() # consume '*'
				comment.write(self.ch())
				break

		out = comment.getvalue()
		comment.close()
		return out


	def write_comment(self, comment):
		# strip comment delimiters, replace newlines with spaces
		comment = re.sub(r"[\r|\n]+", " ", re.sub(self.opts.newline, " ", comment))
		comment = re.sub(r"(\s{2,})", " ", comment)

		# make we should really never have multiple concurrent spaces
		comment = re.sub(self.re_start_comment, "", re.sub(self.re_end_comment, "", comment))

		# word wrap the comment with the correct indentation
		comment = word_wrap(comment, width=self.opts.comment_line_max, keep_separators=False, newline=self.opts.newline)
		has_newlines = comment.count(self.opts.newline) > 0

		# put a blank line above comments if requested and not first write to output
		if(self.opts.blank_line_above_comments and self.written > 0):
			self.write_newline()
		elif(self.written > 0):
			self.write_newline(keep_ws=False)

		if(self.opts.one_line_comments_under_max and not has_newlines):
			self.write("/* " + comment + " */")
		else:
			self.write("/*")

			if(self.opts.indent_comment_body):
				self.indent()

			for line in comment.split(self.opts.newline):
				self.write_newline()
				self.write(line)

			if(self.opts.indent_comment_body):
				self.outdent()

			self.write_newline()
			self.write("*/")

		self.write_newline()

	def eat_string(self, sdelim, edlim):
		string = StringIO()

		# add begining string delimiter to the string buffer if necessary
		if(self.lbb_out.peek_back() != sdelim):
			string.write(sdelim)

		while(self.can_read() and self.read() != None):
			if(self.ch() == "\\"):
				# consume current '\' read the delim value, write it
				string.write(self.read())
				continue
			
			string.write(self.ch())

			# end of string/line
			if(self.ch() == edlim or self.ch() == self.opts.newline):
				break

		sval = string.getvalue()
		string.close()
		return sval

	def write_single_space(self):
		if(self.lbb_out.throughput() > 0 and not self.re_whitespace.match(self.lbb_out.peek_back())):
			self.write(" ")

	def write_left_brace(self, ch):
		self.write_single_space()
		self.write(ch)
		self.write_newline()

	def write_right_brace(self, ch):
		self.outdent()
		self.write_newline(keep_ws=False)
		self.write(ch)
		self.write_newline()
		self.write_newline()

	def write_character(self, ch, prev_ws):
		if(prev_ws and self.lbb_out.peek_back() not in self.opts.no_space_after):
			self.write_single_space()
		self.write(ch)

	def skip_whitespace(self):
		skipped = False
		while(self.re_whitespace.match(self.ch()) and self.can_read()):
			skipped = True
			self.read() # consume the current whitespace character

		return skipped

	def skip_most_whitespace(self):
		while(self.re_whitespace.match(self.ch()) and self.re_whitespace.match(self.input_stream.peek())):
			read()

	def format(self):
		"""do sweet formatting"""
		
		while(self.can_read() and self.read() != None):
			skipped = self.skip_whitespace()
			ch = self.ch()
			
			# comment
			if(ch == "/" and self.input_stream.peek() == "*"):
				comment = self.eat_comment()
				self.write_comment(comment)
			elif(ch == "{"):
				self.indent()
				self.write_left_brace(ch)
			elif(ch == "}"):
				self.write_right_brace(ch)
			elif(ch == "'" or ch == "\""):
				string = self.eat_string(ch, ch)
				self.write(string)
			elif(ch == ";"):
				self.write(ch)
				self.write_newline()
			elif(ch == "("):
				isurl = self.lbb_out.lookback("url")
				self.write(ch)
				ws = False
				if(self.re_whitespace.match(self.input_stream.peek())):
					ws = True
					self.read() # consume current '(' character
					self.skip_whitespace() # skip whitespace

				if(not ws):
					self.read()

				if(self.ch() == "\"" or self.ch() == "'"):
					string = self.eat_string(self.ch(), self.ch())
					self.write(string)
				else:
					c = self.ch()
					string = self.eat_string("(", ")")
					self.write(c)
					self.write(string)
			elif(ch == "," and ch not in self.opts.no_space_after):
				self.write(ch)
				self.write_single_space()
			elif(ch == ":"):
				self.write(ch)
			else:
				self.write_character(ch, skipped)

		self.clear_trailing_whitespace()
		self.indent_level = 0

		if(self.opts.end_with_newline):
			self.write_newline()

		self.flush_output()
		
		if(self.opts.close_input):
			self.close_input()

		if(self.opts.close_output):
			self.close_output()