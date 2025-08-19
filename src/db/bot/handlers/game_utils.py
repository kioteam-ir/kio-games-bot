class GameTypes : 
    XO : int = 1
    C3 : int = 2
    C4 : int = 3
    C5 : int = 4



class EachGame : 
    title:str
    message_text : str
    _id:int # GameTypes
    description : str
    thumb_url : str
    rows : int 
    cols : int 
    connect: int 

    def __init__(self,title:str,message_text:str,_id:int,description:str,thumb_url:str,rows:int,cols:int,connect:int):
        self.title = title
        self.message_text = message_text
        self._id = _id 
        self.description = description
        self.thumb_url = thumb_url
        self.rows = rows
        self.cols = cols
        self.connect = connect

game_lists = {
    1 : EachGame(
            'XO | بازی دایره و ضرب',
            'درحال ساخت بازی ...',
            1,
            "❌⭕️ بازی ضرب در و خانه معروف به دوز ❌⭕️",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Tic_tac_toe.svg/1200px-Tic_tac_toe.svg.png",
            3,3,3
        ),
    2 : EachGame(
            'connect 3 | 3 تاشو وصل کن !',
            'درحال ساخت بازی ...',
            2,
            "🥇 فقط کافیه که 3 تا از مهره هاتو پشت سرهم بچینی. یا افقی یا عمودی و یا ضرب‌دری 🥇",
            "https://lh6.googleusercontent.com/proxy/TYpZrjlqu_tnJvoNtKQHNZXwlxuCbZxEsO_Aq09iS5KAcUDKPaU9mHlr6pLl5Nvyk28rd6y_JoL4aqrxZ0tRQgSKT0ewVMAybrqk20W-UznJCA22AfUyVyTcHm2rRnh18Fa3K5PIXYgSaVs",
            6,7,3
        ),
    3 : EachGame(
            'connect 4 | 4 تاشو وصل کن !',
            'درحال ساخت بازی ...',
            3,
            "🥇 فقط کافیه که 4 تا از مهره هاتو پشت سرهم بچینی. یا افقی یا عمودی و یا ضرب‌دری 🥇",
            "https://www.researchgate.net/profile/Gaetan-Sanchez/publication/258381798/figure/fig1/AS:311148797808643@1451195062476/Traditional-Connect-Four-Here-Red-wins-with-four-coins-aligned-diagonally.png",
            6,7,4
        ),
    4 : EachGame(
            'connect 5 | 5 تاشو وصل کن !',
            'درحال ساخت بازی ...',
            4,
            "🥇 فقط کافیه که 5 تا از مهره هاتو پشت سرهم بچینی. یا افقی یا عمودی و یا ضرب‌دری 🥇",
            "https://static.drimify.com/wp-content/uploads/2024/12/screenshot-415-min.png",
            8,8,5
        ),
}