-- GLOBAL a propósito: Noctalia llama esta función por nombre en cada tick.
function update()
  desktopWidget.setWantsSecondTicks(true) -- refresca justo en el cambio de segundo

  local time_format = noctalia.getConfig("time_format")
  local date_format = noctalia.getConfig("date_format")
  local show_date = noctalia.getConfig("show_date")

  local content = {
    ui.label({
      text = noctalia.formatTime(time_format),
      fontFamily = "Okami",
      fontWeight = "bold",
      fontSize = 32,
      color = "primary",
      baseline = "textFixedHeight",
    }),
  }

  if show_date and date_format then
    table.insert(content, ui.label({
      text = noctalia.formatTime(date_format),
      fontFamily = "Okami",
      fontWeight = "medium",
      fontSize = 11,
      color = "on_surface_variant",
    }))
  end

  desktopWidget.render(ui.column({
    gap = 4,
    align = "center",
    justify = "center",
  }, content))
end
