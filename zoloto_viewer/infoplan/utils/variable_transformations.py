import abc
import html


class Transformation(abc.ABC):
    @abc.abstractmethod
    def apply(self, variables_list, **kwargs):
        pass


def tag_wrap(content, tag, **attrs):
    attrs['class'] = attrs.pop('class_', None)
    attrs_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items() if v is not None)
    return f'<{tag} {attrs_str}>{content}</{tag}>'


class HideMasterPageLine(Transformation):
    def apply(self, variables_list, **kwargs):
        return [var for var in variables_list if not var.startswith('mp:')]


class EliminateTabs(Transformation):
    def apply(self, variables_list, **kwargs):
        return [tag_wrap(var.replace('&amp;tab', '\t'), 'pre') for var in variables_list]


class NewlinesToBr(Transformation):
    def apply(self, variables_list, **kwargs):
        return [var.replace('\n', '<br>') for var in variables_list]


class ReplacePictCodes(Transformation):
    REPLACE_TABLE = [
        ('@WC@', '\ue900'),
        ('@MAN@', '\ue901'),
        ('@WOMAN@', '\ue902'),
        ('@MGN@', '\ue903'),
        ('@BABY@', '\ue904'),
        ('@CAFE@', '\ue905'),
        ('@BAR@', '\ue906'),
        ('@FOOD@', '\ue907'),
        ('@CLOAKROOM@', '\ue908'),
        ('@LIFT@', '\ue909'),
        ('@SHOP@', '\ue90a'),
        ('@MEET@', '\ue90b'),
        ('@CART@', '\ue90c'),
        ('@SAFE@', '\ue90d'),
        ('@PLAYGROUND@', '\ue90e'),
        ('@CARWASH@', '\ue90f'),
        ('@BUS@', '\ue910'),
        ('@RAILROAD@', '\ue911'),
        ('@POLICE@', '\ue912'),
        ('@ESCALATE@', '\ue913'),
        ('@STAIRS@', '\ue914'),
        ('@CHARGE@', '\ue915'),
        ('@BANK@', '\ue916'),
        ('@P@', '\ue917'),
        ('@MEDIC@', '\ue918'),
        ('@INFO@', '\ue919'),
        ('@NOSMOKE@', '\ue91a'),
        ('@NOALCO@', '\ue91b'),
        ('@STOP@', '\ue91c'),
        ('@TICKETS@', '\ue91d'),
        ('@VOLLEY@', '\ue91e'),
        ('@FOOTBALL@', '\ue91f'),
        ('@HOCKEY@', '\ue920'),
        ('@BASKET@', '\ue921'),
        ('@TENNIS@', '\ue922'),
        ('@ICESKATE@', '\ue923'),
        ('@PRINT@', '\ue924'),
        ('@MAN_CLO@', '\ue925'),
        ('@WOMAN_CLO@', '\ue926'),
        ('@SHOWER@', '\ue927'),
        ('@MAN_SHO@', '\ue928'),
        ('@WOMAN_SHO@', '\ue929'),
        ('@WALK@', '\ue92a'),
        ('@BIKE@', '\ue92b'),
        ('@WORKOUT@', '\ue92c'),
        ('@DOG@', '\ue92d'),
        ('@SKATE@', '\ue92e'),
        ('@ELECTRO@', '\ue92f')
    ]
    REPLACE_DICT = dict(REPLACE_TABLE)

    def substitute_pict_codes(self, var):
        for code, pict in self.REPLACE_DICT.items():
            if code in var:
                var = var.replace(code, tag_wrap(pict, 'span', class_='infoplan_icon'))
        return var

    def apply(self, variables_list, **kwargs):
        return [self.substitute_pict_codes(var) for var in variables_list]


def html_escape_incoming(vars_by_side):
    def _escape(vars_list):
        return [html.escape(v) for v in vars_list]

    return {side: _escape(variables_list)
            for side, variables_list in vars_by_side.items()}
