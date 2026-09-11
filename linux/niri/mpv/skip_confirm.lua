-- skip_confirm.lua
-- Muestra un aviso con countdown antes de saltar capitulos de Opening/Ending.
-- El cancelar el salto se hace con un Custom Command de Haruna (script-message-to),
-- NO con una tecla capturada directamente por el script -- Haruna intercepta
-- teclas comunes (como SPACE) antes de que lleguen al script.
--
-- NOTA: usamos create_osd_overlay en vez de mp.osd_message porque Haruna
-- renderiza los mensajes de osd_message en su propio cuadro de texto plano
-- (ignora los tags ASS). El overlay en cambio lo dibuja mpv directamente
-- sobre el video, igual que un subtitulo, asi que si respeta el estilo.

local skip_patterns = { "opening", "ending", "op", "ed" }  -- palabras clave (minusculas)
local countdown = 5  -- segundos antes de saltar

-- Estilo del aviso, con tags ASS (el mismo formato de los subtitulos .ass).
-- \an7         -> posicion: arriba izquierda
-- \fs46        -> tamano de fuente
-- \b1          -> negrita
-- \i1           -> Cursiva
-- \&HFFFFFF&  -> color de relleno del texto en formato BGR: blanco
-- \3c&H000000& -> color del contorno (outline): negro
-- \bord3       -> grosor del contorno
-- \shad1       -> sombra chiquita, da el toque "subtitulo de streaming"
local osd_style = "{\\an7\\fs46\\b1\\i1\\&HFFFFFF&\\3c&H000000&\\bord3\\shad1}"

local overlay = mp.create_osd_overlay("ass-events")
local hide_timer = nil
local skip_timer = nil
local current_chapter_index = nil

local function show_message(text, duration)
    if hide_timer then
        hide_timer:kill()
        hide_timer = nil
    end
    overlay.data = osd_style .. text
    overlay:update()
    hide_timer = mp.add_timeout(duration, function()
        overlay:remove()
        hide_timer = nil
    end)
end

local function chapter_matches(title)
    if not title then return false end
    local lower = title:lower()
    for _, pat in ipairs(skip_patterns) do
        if lower:find(pat, 1, true) then
            return true
        end
    end
    return false
end

local function cancel_skip()
    if skip_timer then
        skip_timer:kill()
        skip_timer = nil
        show_message("Salto cancelado", 1)
    end
end

local function do_skip()
    skip_timer = nil
    if hide_timer then
        hide_timer:kill()
        hide_timer = nil
    end
    overlay:remove()
    mp.commandv("add", "chapter", 1)
end

local function on_chapter_change(_, chapter_index)
    if chapter_index == nil or chapter_index == current_chapter_index then
        return
    end
    current_chapter_index = chapter_index

    local chapters = mp.get_property_native("chapter-list")
    if not chapters or not chapters[chapter_index + 1] then
        return
    end

    local title = chapters[chapter_index + 1].title
    if chapter_matches(title) then
        local msg = string.format(
            "Saltando '%s' en %ds... [C] para cancelar",
            title, countdown
        )
        show_message(msg, countdown + 0.5)
        skip_timer = mp.add_timeout(countdown, do_skip)
    end
end

-- "cancel_skip" es el arg1 que usas en el Custom Command de Haruna
mp.register_script_message("cancel_skip", cancel_skip)
mp.observe_property("chapter", "number", on_chapter_change)
