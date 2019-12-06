import os
import logging

app_home = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".."))


def get_logger(modname: str) -> logging.Logger:
    """
    * 引数のモジュールごとにloggerオブジェクトを生成する
    :param modname:
    :return logger:
    """
    # loggerを作成する
    logger = logging.getLogger(modname)

    # ログフォーマット
    _formatting = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # StreamHandlerを生成してルートロガーに追加し、ロギングシステムの基本的な環境設定を行う
    # defaultのログレベルはlevel=logging.WARNING
    # 開発中、開発環境はDEBUG
    logging.basicConfig(
        level=logging.DEBUG,
        format=_formatting,
    )

    # モジュールごとにログレベルを個別設定
    logging.getLogger("botocore").setLevel(level=logging.WARNING)
    logging.getLogger("boto3").setLevel(level=logging.WARNING)
    logging.getLogger("urllib3").setLevel(level=logging.WARNING)

    return logger
