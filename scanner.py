import io
import os
import re
from StringIO import StringIO
from collections import deque


class Scanner(object):
	"""base scanner"""
	def __init__(self, source, output):		
		super(Scanner, self).__init__()
		
		source_type = type(source)
		self.re_whitespace = re.compile(r"^\s+$")

		if(source_type == str or source_type == unicode):
			self.input_stream = StringInput(source)
		elif(source_type == file):
			self.input_stream = FileInput(source)
		else:
			raise ValueError("'source' arument must be a string/unicode or file handle")

		self.output_stream = output
		self.lbb_out = LookbackBuffer()
		self.lbb_in = LookbackBuffer()
		self.written = 0

	def read(self):
		"""read a single character from the input stream"""
		if(not self.input_stream.ready()):
			return None
		else:
			c = self.input_stream.read()
			self.lbb_in.write(c) # add the character to the input stream lookback buffer
			return c

	def ch(self):
		"""return the current/last character read from the input stream"""
		return self.input_stream.ch()

	def can_read(self):
		"""returns True if the input stream has remaining characters available to be read, else False"""
		return self.input_stream.ready()

	def write(self, s):
		"""write a string to the output stream and update the output lookback-buffer"""
		self.written += len(s) # increment the throughput counter
		self.lbb_out.write(s) # add character sequence to the output lookback buffer
		self.output_stream.write(s)

	def clear_trailing_whitespace(self):
		"""clear all whitespace characters from the tail of the output stream's current position"""
		pre_pos = self.output_stream.tell()
		back = 1
		while(self.re_whitespace.match(self.lbb_out.peek_back(back))):
			back += 1

		if(back > 1): 
			self.lbb_out.pop(back) #truncate the lookback buffer to keep it accurate
			self.output_stream.truncate(self.output_stream.tell() - back + 1) # get rid of the whitespace
			self.output_stream.seek(pre_pos - back + 1) # reset the output stream to the correct position

	def flush_output(self):
		"""flush the output and then call fsync if possible"""
		self.output_stream.flush()
		if(hasattr(self.output_stream, "fsync")):
			self.output_stream.fsync()

	def close_input(self):
		"""closes the input stream"""
		self.input_stream.close()

	def close_output(self):
		self.output_stream.close()

	def close(self):
		self.close_input()
		self.close_output()

class InputSource(object):
	"""base text input class definition/interface"""
	def __init__(self):
		super(InputSource, self).__init__()

	def read(self):
		"""read a single character from the input source"""
		raise NotImplementerError()

	def ch(self):
		"""return the current character/last character read"""
		raise NotImplementerError()

	def peek(self, amount=1):
		"""peek forward in the input stream by X amount"""
		raise NotImplementerError()

	def ready(self):
		"""input stream has remaining characters to read"""
		raise NotImplementerError()

	def close(self):
		"""close the input stream"""
		pass

class StringInput(InputSource):
	"""input class for in memory strings"""
	def __init__(self, source, max_look_behind=50):
		super(StringInput, self).__init__()

		self.source = source
		self.source_length = len(source)		
		self.pos = -1

	def read(self):
		if(not self.ready()):
			return None

		self.pos += 1
		next = self.source[self.pos]
		
		return next

	def ch(self):
		return self.source[self.pos]

	def peek(self, amount=1):
		if(not self.ready()):
			return None
			
		return self.source[self.pos+1:self.pos+amount+1]	

	def ready(self):
		return self.pos < self.source_length-1

	def close(self):
		pass


class FileInput(InputSource):	
	"""input class for file input sources"""
	def __init__(self, input_stream, max_look_behind=50):
		super(FileInput, self).__init__()

		self.source = input_stream
		self.source_length = os.fstat(input_stream.fileno()).st_size
		self.pos = -1
		self.cur_char = None

	def read(self):
		if(not self.ready()):
			return None

		self.cur_char = self.source.read(1)
		return self.cur_char

	def ch(self):
		return self.cur_char

	def peek(self, amount=1):
		if(not self.ready()):
			return None
			
		start_pos = self.source.tell()
		peek = self.source.read(amount)
		self.source.seek(start_pos)

		return peek

	def ready(self):
		return self.source.tell() < self.source_length

	def close(self):
		self.source.close()


class LookbackBuffer(object):
	"""lookback buffer"""
	def __init__(self, src="", max_len = 5000):
		super(LookbackBuffer, self).__init__()

		self.max_len = max_len
		l = len(src)

		if(l > self.max_len):
			src = src[l-max_len:]

		self.q = deque(list(src))
		self.history_size = len(self.q)

	def write(self, s):
		for char in s:
			self.write_char(char)

	def write_char(self, s):
		self.history_size = self.history_size + 1

		if(self.size() == self.max_len):
			self.q.popleft()

		self.q.append(s)

	def to_string(self):
		return "".join(self.q)

	def lookback(self, s, back=None):
		if(back == None):
			back = len(s)

		peek = self.peek_back(back)
		return s == peek
	
	def peek_back(self, back=1):
		if(back < 1):
			raise ValueError("back value must be >= 1")

		s = self.size()

		if(s < back):
			back = s

		return "".join(list(self.q)[-back:])

	def pop(self, back):
		for x in range(0,back):
			self.q.pop()
			self.history_size -= 1

	def size(self):
		return len(self.q)

	def throughput(self):
		return self.history_size