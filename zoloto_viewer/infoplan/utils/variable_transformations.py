import abc
import html
import re

from zoloto_viewer.infoplan.models import MarkerVariable


class Transformation(abc.ABC):
    @abc.abstractmethod
    def apply(self, variables_list, **kwargs):
        pass


class PerOneTransformation(Transformation):
    @abc.abstractmethod
    def per_variable(self, var, **kwargs):
        pass

    def apply(self, variables_list, **kwargs):
        return [self.per_variable(var, **kwargs) for var in variables_list]


def tag_wrap(content, tag, **attrs):
    attrs['class'] = attrs.pop('class_', None)
    attrs_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items() if v is not None)
    return f'<{tag} {attrs_str}>{content}</{tag}>'


class HideMasterPageLine(Transformation):
    def apply(self, variables_list, **kwargs):
        return [var for var in variables_list if not var.startswith('mp:')]


class UnescapeTabs(PerOneTransformation):
    def per_variable(self, var, **kwargs):
        return tag_wrap(var.replace('&amp;tab', '\t'), 'pre')


class UnescapeTabsText(PerOneTransformation):
    def per_variable(self, var, **kwargs):
        return var.replace('&tab', '\t')


class EliminateTabs(PerOneTransformation):
    def per_variable(self, var, **kwargs):
        return var.replace('&tab', '')


class NewlinesToBr(PerOneTransformation):
    def per_variable(self, var, **kwargs):
        return var.replace('\n', '<br>')


class UnescapeHtml(PerOneTransformation):
    def per_variable(self, var, **kwargs):
        return html.unescape(var)


class ReplacePictCodes(PerOneTransformation):
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
    DEFAULT_PICT = '\u25fb'
    REPLACE_DICT = dict(REPLACE_TABLE)

    def substitute_pict_codes(self, var):
        used = re.findall(MarkerVariable.PICT_PATTERN, var)
        for code in used:
            pict = self.REPLACE_DICT.get(code, self.DEFAULT_PICT)
            var = var.replace(code, tag_wrap(pict, 'span', class_='infoplan_icon'))
        return var

    def per_variable(self, var, **kwargs):
        return self.substitute_pict_codes(var)


class EliminatePictCodes(PerOneTransformation):
    PICT_REGEX = re.compile(MarkerVariable.PICT_PATTERN)

    def per_variable(self, var, **kwargs):
        return re.sub(self.PICT_REGEX, '', var)


class EliminateNumbers(PerOneTransformation):
    NUMBER_PERIODS_REGEX = r'\d+…\d+|\d+\.\.\.?\d+|\d+'

    def per_variable(self, var, **kwargs):
        return re.sub(self.NUMBER_PERIODS_REGEX, '', var)


def html_escape_incoming(vars_by_side):
    def _escape(vars_list):
        return [html.escape(v) for v in vars_list]

    return {side: _escape(variables_list)
            for side, variables_list in vars_by_side.items()}
