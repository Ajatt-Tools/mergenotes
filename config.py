from anki.cards import Card
from anki.notes import Note
from aqt import mw


def due_key(card: Card) -> tuple:
    # sort cards by their type, then by due number,
    # so that new cards are always in the beginning of the list,
    # mimicking the way cards are presented in the Anki Browser
    return card.type, card.due


def sort_field_key(card: Card) -> str:
    note: Note = card.note()
    return note.values()[note.model()['sortf']]


class OrderingChoices:
    __choices = {
        "Due": due_key,
        "Sort Field": sort_field_key
    }

    @classmethod
    def get_key(cls, key):
        return cls.__choices.get(key)

    @classmethod
    def as_list(cls):
        return [*cls.__choices.keys()]


def get_config() -> dict:
    cfg: dict = mw.addonManager.getConfig(__name__)
    cfg['delete_original_notes']: bool = cfg.get('delete_original_notes', False)
    cfg['merge_tags']: bool = cfg.get('merge_tags', True)
    cfg['only_empty']: bool = cfg.get('only_empty', False)
    cfg['reverse_order']: bool = cfg.get('reverse_order', False)
    cfg['field_separator']: str = cfg.get('field_separator', "")
    cfg['shortcut']: str = cfg.get('shortcut', "Ctrl+Alt+M")
    cfg['ordering']: str = cfg.get('ordering', "Due")

    if not cfg['ordering'] in OrderingChoices.as_list():
        print('Wrong ordering:', cfg['ordering'])
        cfg['ordering'] = OrderingChoices.get_key("Due")

    return cfg


config = get_config()


def write_config():
    return mw.addonManager.writeConfig(__name__, config)
