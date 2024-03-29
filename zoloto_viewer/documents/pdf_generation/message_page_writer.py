from . import layout
from .message import MessagesAreaFreeBox, MessageElem


class MessagePageWriter(layout.BasePageWriterDeducingTitle):
    def __init__(self, canvas, floor, layers, marker_messages_getter):
        self.floor = floor
        self.layers = layers
        self._marker_messages = marker_messages_getter(floor, layers)
        super().__init__(canvas)

    def write(self):
        self.draw_header()
        self.draw_footer()
        try:
            self.draw_content()
        except layout.NotEnoughSpaceException:
            self.canvas.showPage()
            self.write()

    def make_page_title(self):
        title = [
            f'Монтажная область {self.floor.file_title}. {self.floor.level_subtitle}',
            ''
        ]
        return title

    def make_page_super_title(self):
        super_title = [self.floor.project.title, self.floor.project.stage]
        return super_title

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
