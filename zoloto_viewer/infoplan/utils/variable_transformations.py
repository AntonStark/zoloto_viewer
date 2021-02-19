import abc


class Transformation(abc.ABC):
    @abc.abstractmethod
    def apply(self, variables_list, **kwargs):
        pass


class HideMasterPageLine(Transformation):
    def apply(self, variables_list, **kwargs):
        return [var for var in variables_list if not var.startswith('mp:')]


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
                var = var.replace(code, pict)
        return var

    def apply(self, variables_list, **kwargs):
        return [self.substitute_pict_codes(var) for var in variables_list]
