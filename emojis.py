class Emojis():
    emojis = {
        ':+1:': u'\U0001F44D',
    }

    @staticmethod
    def get(emoji_code):
        """
        Returns the given emoji's unicode string.
        The *emoji_code* should be as represented at Telegram web
        """
        return Emojis.emojis.get(emoji_code, emoji_code)
