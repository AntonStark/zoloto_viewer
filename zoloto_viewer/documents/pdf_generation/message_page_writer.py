from . import layout
from .message import calc_variable_metrics, MessagesArea, MessageBox


class MessagePageWriter(layout.BasePageWriter):
    _marker_messages = None
    _marker_sides = None
    _layer_color = None

    def __init__(self, canvas, title, super_title,
                 marker_messages, marker_sides, layer_color):
        super().__init__(canvas, title, super_title)
        self.set_params(marker_messages, marker_sides, layer_color)

    def draw_content(self):
        def chunk(seq, n):
            for i in range(0, len(seq), n):
                yield seq[i:i + n]

        # marker_messages: [ ( number, [(side, vars_list)] ), ]
        var_lines, max_var_count = calc_variable_metrics(self._marker_messages)
        message_box = MessageBox(self.canvas, var_lines, max_var_count, self._marker_sides)
        box_size = message_box.get_size()

        area_width, area_height = layout.mess_area_size()
        area_left, area_bottom = layout.mess_area_position()
        area = MessagesArea(area_width, area_height, message_box)

        without_comment_lines = 0
        batch_size = area.column_count()
        for mess_chunk in chunk(self._marker_messages, batch_size):
            positions = area.place_row(without_comment_lines)
            if not positions:
                self.canvas.showPage()
                self.draw_header()
                self.draw_footer()

                area.reset()
                positions = area.place_row(without_comment_lines)
            if not positions:
                area.error_message(self.canvas, mess_chunk)

            for (number, infoplan), (offset_x, offset_y) in zip(mess_chunk, positions):
                box_offset = area_left + offset_x, area_bottom + offset_y
                message_box.draw_message_v2(self.canvas, number, infoplan, box_offset, box_size, self._layer_color)

    def set_params(self, marker_messages, marker_sides, layer_color):
        self._marker_messages = marker_messages
        self._marker_sides = marker_sides
        self._layer_color = layer_color


def message_pages(canvas, marker_messages, marker_sides, layer_color, title, super_title):
    writer = MessagePageWriter(canvas, title, super_title, marker_messages, marker_sides, layer_color)
    writer.write()

# place_row_or_raise
# todo handle layout.NotEnoughSpaceException and continue from where left off
# todo 2 повторная ошибка должна давать сообщение об ошибке
