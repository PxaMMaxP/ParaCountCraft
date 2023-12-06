-- RandziffernFilter.lua
local count = 1
local lastCount = 1 -- Variable um den letzten Zählerwert zu speichern
local chapter = 0
local indexUserID = {}
local resetAtChapter = false
local chapterSep = "."
local enclosingChars = {"[", "]"} -- Standardmäßig '[]' als einschließende Zeichen

function countPara(doc)
  for i, elem in ipairs(doc.blocks) do
    -- Kapitel zurücksetzen, wenn nötig
    if elem.t == "Header" and elem.level == 1 and not elem.classes:includes("unnumbered") and resetAtChapter then
      chapter = chapter + 1
      count = 1
	  lastCount = 1
    end

    if elem.t == "Para" and not (elem.content[1] and elem.content[1].t == "Image") then
      local ID = resetAtChapter and (chapter .. chapterSep .. count) or count
      local userID = nil
      local extraChar = nil
		
      -- Prüfe auf benutzerdefinierte IDs und extra Zeichen am Ende des Absatzes
      if elem.content[#elem.content].t == "Str" then
        local str = elem.content[#elem.content].text
        -- Extrahiere die benutzerdefinierte ID
        userID = str:match("{#rz:([^}]*)}")
        if userID and userID ~= "" then
          indexUserID[userID] = ID
          str = str:gsub("{#rz:" .. userID .. "}", "")
        end
        -- Extrahiere das extra Zeichen
        extraChar = str:match("{.extraPara%-([A-Za-z])}")
        if extraChar then
          -- Verwende den letzten Zählerwert und füge das extra Zeichen hinzu
          ID = resetAtChapter and (chapter .. chapterSep .. lastCount .. extraChar) or lastCount .. extraChar
          str = str:gsub("{.extraPara%-" .. extraChar .. "}", "")
        end
        -- Aktualisiere den Text des letzten Elements
        if userID or extraChar then
          elem.content[#elem.content].text = str
          -- Entferne das vorangehende Leerzeichen, wenn vorhanden
          if #elem.content > 1 and elem.content[#elem.content - 1].t == "Space" then
            table.remove(elem.content, #elem.content - 1)
          end
        end
      end

      -- Füge die Randziffer mit LaTeX am Anfang des Absatzes ein
      local texCount = "\\randziffer{" .. enclosingChars[1] .. ID .. enclosingChars[2] .. "}"
      if userID and userID ~= "" then
        texCount = "\\label{rz:" .. userID .. "}{" .. texCount .. "}"
	  else
	    texCount = "\\label{rz:" .. ID .. "}{" .. texCount .. "}"
      end
      table.insert(elem.content, 1, pandoc.RawInline('tex', texCount))

      -- Speichere den aktuellen Zählerwert als letzten Wert, bevor er möglicherweise erhöht wird
      lastCount = count

      -- Inkrementiere den Zähler nur, wenn kein extra Zeichen gefunden wurde
      if not extraChar then
        count = count + 1
      end
    end
  end
  return pandoc.Pandoc(doc.blocks, doc.meta)
end

return {
  {Pandoc = countPara}
}
