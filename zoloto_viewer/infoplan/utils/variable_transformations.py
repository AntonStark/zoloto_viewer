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
        ('@CLO@', '\ue908'),
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
        ('@MED@', '\ue918'),
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
        ('@ELECTRO@', '\ue92f'),
        ('@S0@', '\ue917'),
        ('@S1@', '\ue930'),
        ('@S2@', '\ue931'),
        ('@S3@', '\ue932'),
        ('@S4@', '\ue933'),
        ('@S5@', '\ue934'),
        ('@S6@', '\ue935'),
        ('@S7@', '\ue936'),
        ('@S8@', '\ue937'),
        ('@S9@', '\ue938'),
        ('@S10@', '\ue939'),
        ('@S11@', '\ue93a'),
        ('@S12@', '\ue93b'),
        ('@S13@', '\ue93c'),
        ('@S14@', '\ue93d'),
        ('@S15@', '\ue93e'),
        ('@S16@', '\ue93f'),
        ('@S17@', '\ue940'),
        ('@S18@', '\ue941'),
        ('@S19@', '\ue942'),
        ('@S20@', '\ue943'),
        ('@S21@', '\ue944'),
        ('@S22@', '\ue945'),
        ('@S23@', '\ue946'),
        ('@S24@', '\ue947'),
        ('@S25@', '\ue948'),
        ('@S26@', '\ue949'),
        ('@S27@', '\ue94a'),
        ('@S28@', '\ue94b'),
        ('@S29@', '\ue94c'),
        ('@S30@', '\ue94d'),
        ('@S31@', '\ue94e'),
        ('@S32@', '\ue94f'),
        ('@S33@', '\ue950'),
        ('@S34@', '\ue951'),
        ('@S35@', '\ue952'),
        ('@S36@', '\ue953'),
        ('@S37@', '\ue954'),
        ('@S38@', '\ue955'),
        ('@S39@', '\ue956'),
        ('@S40@', '\ue957'),
        ('@S41@', '\ue958'),
        ('@S42@', '\ue959'),
        ('@S43@', '\ue95a'),
        ('@S44@', '\ue95b'),
        ('@S45@', '\ue95c'),
        ('@S46@', '\ue95d'),
        ('@S47@', '\ue95e'),
        ('@S48@', '\ue95f'),
        ('@S49@', '\ue960'),
        ('@S50@', '\ue961'),
        ('@SA@', '\ue962'),
        ('@SB@', '\ue963'),
        ('@SC@', '\ue964'),
        ('@SD@', '\ue965'),
        ('@SE@', '\ue966'),
        ('@SF@', '\ue967'),
        ('@SG@', '\ue968'),
        ('@SH@', '\ue969'),
        ('@SI@', '\ue96a'),
        ('@SJ@', '\ue96b'),
        ('@SK@', '\ue96c'),
        ('@SL@', '\ue96d'),
        ('@SM@', '\ue96e'),
        ('@SN@', '\ue96f'),
        ('@SO@', '\ue970'),
        ('@SP@', '\ue971'),
        ('@SQ@', '\ue972'),
        ('@SR@', '\ue973'),
        ('@SS@', '\ue974'),
        ('@ST@', '\ue975'),
        ('@SU@', '\ue976'),
        ('@SV@', '\ue977'),
        ('@SW@', '\ue978'),
        ('@SX@', '\ue979'),
        ('@SY@', '\ue97a'),
        ('@SZ@', '\ue97b'),
        ('@0@', '\ue97c'),
        ('@1@', '\ue97d'),
        ('@2@', '\ue97e'),
        ('@3@', '\ue97f'),
        ('@4@', '\ue980'),
        ('@5@', '\ue981'),
        ('@6@', '\ue982'),
        ('@7@', '\ue983'),
        ('@8@', '\ue984'),
        ('@9@', '\ue985'),
        ('@10@', '\ue986'),
        ('@11@', '\ue987'),
        ('@12@', '\ue988'),
        ('@13@', '\ue989'),
        ('@14@', '\ue98a'),
        ('@15@', '\ue98b'),
        ('@16@', '\ue98c'),
        ('@17@', '\ue98d'),
        ('@18@', '\ue98e'),
        ('@19@', '\ue98f'),
        ('@20@', '\ue990'),
        ('@21@', '\ue991'),
        ('@22@', '\ue992'),
        ('@23@', '\ue993'),
        ('@24@', '\ue994'),
        ('@25@', '\ue995'),
        ('@26@', '\ue996'),
        ('@27@', '\ue997'),
        ('@28@', '\ue998'),
        ('@29@', '\ue999'),
        ('@30@', '\ue99a'),
        ('@31@', '\ue99b'),
        ('@32@', '\ue99c'),
        ('@33@', '\ue99d'),
        ('@34@', '\ue99e'),
        ('@35@', '\ue99f'),
        ('@36@', '\ue9a0'),
        ('@37@', '\ue9a1'),
        ('@38@', '\ue9a2'),
        ('@39@', '\ue9a3'),
        ('@40@', '\ue9a4'),
        ('@41@', '\ue9a5'),
        ('@42@', '\ue9a6'),
        ('@43@', '\ue9a7'),
        ('@44@', '\ue9a8'),
        ('@45@', '\ue9a9'),
        ('@46@', '\ue9aa'),
        ('@47@', '\ue9ab'),
        ('@48@', '\ue9ac'),
        ('@49@', '\ue9ad'),
        ('@50@', '\ue9ae'),
        ('@A@', '\ue9af'),
        ('@B@', '\ue9b0'),
        ('@C@', '\ue9b1'),
        ('@D@', '\ue9b2'),
        ('@E@', '\ue9b3'),
        ('@F@', '\ue9b4'),
        ('@G@', '\ue9b5'),
        ('@H@', '\ue9b6'),
        ('@I@', '\ue9b7'),
        ('@J@', '\ue9b8'),
        ('@K@', '\ue9b9'),
        ('@L@', '\ue9ba'),
        ('@M@', '\ue9bb'),
        ('@N@', '\ue9bc'),
        ('@O@', '\ue9bd'),
        ('@P@', '\ue9be'),
        ('@Q@', '\ue9bf'),
        ('@R@', '\ue9c0'),
        ('@S@', '\ue9c1'),
        ('@T@', '\ue9c2'),
        ('@U@', '\ue9c3'),
        ('@V@', '\ue9c4'),
        ('@W@', '\ue9c5'),
        ('@X@', '\ue9c6'),
        ('@Y@', '\ue9c7'),
        ('@Z@', '\ue9c8'),
        ('@←@', '\ue9c9'),
        ('@↖@', '\ue9ca'),
        ('@↑@', '\ue9cb'),
        ('@↗@', '\ue9cc'),
        ('@→@', '\ue9cd'),
        ('@↘@', '\ue9ce'),
        ('@↓@', '\ue9cf'),
        ('@↙@', '\ue9d0'),
        ('@…@', '\ue9d1'),
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


class EliminateArrows(PerOneTransformation):
    ARROWS_REGEX = r'[\u2190-\u2199]+'

    def per_variable(self, var, **kwargs):
        return re.sub(self.ARROWS_REGEX, '', var)


def html_escape_incoming(vars_by_side):
    def _escape(vars_list):
        return [html.escape(v) for v in vars_list]

    return {side: _escape(variables_list)
            for side, variables_list in vars_by_side.items()}
