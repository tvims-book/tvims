local function raw(s) return pandoc.RawBlock('latex', s) end
local function verb(env, text)
  return raw('\\begin{' .. env .. '}\n\\begin{Verbatim}[breaklines,breakanywhere,fontsize=\\small]\n' .. text .. '\n\\end{Verbatim}\n\\end{' .. env .. '}')
end
function CodeBlock(b)
  if b.classes:includes('python') then
    local env = b.classes:includes('solution') and 'solbox' or 'codebox'
    return {raw('\\begin{' .. env .. '}'), b, raw('\\end{' .. env .. '}')}
  end
  if b.classes:includes('stdin') then return verb('inbox', b.text) end
  if b.classes:includes('text') then return verb('plainbox', b.text) end
  if #b.classes > 0 then return verb('plainbox', b.text) end
  return verb('outbox', b.text)
end
function BlockQuote(b)
  return {raw('\\begin{rulebox}')} .. b.content .. {raw('\\end{rulebox}')}
end
function HorizontalRule() return {} end
local DIVS = {
  ['определение'] = 'defbox', ['теорема'] = 'thmbox', ['пример'] = 'exbox',
  ['ошибка'] = 'errbox', ['проверь-себя'] = 'chkbox',
  definition = 'defbox', theorem = 'thmbox', example = 'exbox', mistake = 'errbox', check = 'chkbox',
}
function Div(d)
  for _, c in ipairs(d.classes) do
    local env = DIVS[c]
    if env then
      return {raw('\\begin{' .. env .. '}')} .. d.content .. {raw('\\end{' .. env .. '}')}
    end
  end
end
