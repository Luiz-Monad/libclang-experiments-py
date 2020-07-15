import sys, pprint
from libclang.cindex import TranslationUnit, Index, SourceLocation, Cursor, File, CursorKind, TypeKind, Config, LibclangError

pp = pprint.PrettyPrinter(indent=4)

def getQuickFix(diagnostic):
  # Some diagnostics have no file, e.g. "too many errors emitted, stopping now"

  if diagnostic.location.file:
    filename = diagnostic.location.file.name
  else:
    filename = ""

  if diagnostic.severity == diagnostic.Ignored:
    type = 'I'
  elif diagnostic.severity == diagnostic.Note:
    type = 'I'
  elif diagnostic.severity == diagnostic.Warning:
    type = 'W'
  elif diagnostic.severity == diagnostic.Error:
    type = 'E'
  elif diagnostic.severity == diagnostic.Fatal:
    type = 'E'
  else:
    return None

  res = dict({ 
    'buf':  filename,
    'line': diagnostic.location.line,
    'col': diagnostic.location.column,
    'text': diagnostic.spelling,
    'type': type
  })
  return res

def getQuickFixList(tu):
  return filter(None, map(getQuickFix, tu.diagnostics))

def notry(f):
  try:
    return f()
  except:
    return None

def filterDict(d):
  return { k: v for (k, v) in d.items() if v != None }
  
def getArgs(args):
  return map(getType, args)

def getType(c):
  if c.kind == TypeKind.INVALID: return None
  return filterDict({
    'kind': notry(lambda: c.kind),
    'spelling': notry(lambda: c.spelling),
    'args': notry(lambda: getArgs(c.argument_types())),
    'elem_type': notry(lambda: c.element_type),
    'elems': notry(lambda: c.element_count),
    'result_type': notry(lambda: getType(c.get_result())),
    'arr_size': notry(lambda: c.get_array_size()),
    'arr_type': notry(lambda: getType(c.get_array_element_type())),
    'cls_type': notry(lambda: getType(c.get_class_type())),
    'named_type': notry(lambda: getType(c.get_named_type())),
    #'align': notry(lambda: c.get_align()),
    'size': notry(lambda: c.get_size()),
  })

def getReferences(cs):
    refs = []
    for c in cs:
      if c.location.file is None:
        pass
      else: #if c.kind == CursorKind.OBJC_PROTOCOL_DECL:
        refs.append(filterDict({
          'kind': c.kind,
          'spelling': c.spelling,
          #'displayname': c.displayname,
          #'mangled_name': c.mangled_name,
          'line': c.location.line,
          'col': c.location.column,
          #'storage': c.storage_class,
          'access': c.access_specifier,
          'type': getType(c.type),
          'result_type': getType(c.result_type),
          #'typedef_type': getType(c.underlying_typedef_type),
          #'objc_enc': c.objc_type_encoding,
          #'comment': c.brief_comment,
          #'raw': c.raw_comment,
          'args': getReferences(c.get_arguments()),
        }))
    return refs

def walk(tu, f):
  return f(tu.cursor.walk_preorder())

def init():
  conf = Config()

  # here we use the libclang.dylib from the vim plugin -- YouCompleteMe
  libclangPath = "."
  Config.set_library_path(libclangPath)
  conf.set_library_path(libclangPath)
  try:
    conf.get_cindex_library()
  except LibclangError as e:
    print "Error: " + str(e)

def main():
    #sysroot = '/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk',
    sysroot = '/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneSimulator.platform/Developer/SDKs/iPhoneSimulator.sdk'
    #arch = 'arm64'
    arch = 'x86_64'
    opt = TranslationUnit.PARSE_KEEPGOING
    cargs = [
      #'-v',
      '-x', 'objective-c',
      '-arch', arch,
      '-fmodules', 
      '-gmodules',
      '-sdk', 'iphonesimulator',
      '-miphoneos-version-min=9.3',
      '-isysroot', sysroot,
    ]
    init()
    index = Index.create()
    files = ['pre.h'] + sys.argv[1:]
    for f in files:
      tu = index.parse(f, args = cargs, options = opt)
      pp.pprint(f)
      pp.pprint(getQuickFixList(tu))
      pp.pprint(walk(tu, getReferences))    

if __name__ == '__main__':
    main()
