from . import layout
from .message import MessagesAreaFreeBox, MessageElem


class MessagePageWriter(layout.BasePageWriter):
    _marker_messages = None

    def __init__(self, canvas, title, super_title, marker_messages):
        super().__init__(canvas, title, super_title)
        self.set_params(marker_messages)

    def write(self):
        self.draw_header()
        self.draw_footer()
        try:
            self.draw_content()
        except layout.NotEnoughSpaceException:
            self.canvas.showPage()
            self.write()

    def draw_content(self):
        area_width, area_height = layout.mess_area_size()
        area_left, area_bottom = layout.mess_area_position()
        area = MessagesAreaFreeBox(area_width, area_height)

        while self._marker_messages:
            message: MessageElem = self._marker_messages.pop(0)
            message.set_canvas(self.canvas)
            try:
                offset_left, offset_bottom = area.place_message(message.get_width(), message.get_height())
            except layout.TooLargeMessageException:
                area.error_message(self.canvas, message)
                continue
            except layout.NotEnoughSpaceException:
                self._marker_messages.insert(0, message)
                raise
            box_offset = area_left + offset_left, area_bottom + offset_bottom
            message.draw(box_offset)

    def set_params(self, marker_messages):
        self._marker_messages = marker_messages


def message_pages(canvas, marker_messages, title, super_title):
    writer = MessagePageWriter(canvas, title, super_title, marker_messages)
    writer.write()
