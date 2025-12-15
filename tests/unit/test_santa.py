from omar_bot.services.santa_v2 import SantaService
from omar_bot.config.settings import USERS_DIR
from omar_bot.services.user_service import UserService


def test_1():
    user_service = UserService(users_dir=USERS_DIR)
    santa_service = SantaService(user_service, group_name="santa")
    pairings = santa_service.get_pairings()

    for gifter_id, correct_giftee_id in pairings.items():
        gifter_name = santa_service.get_user_name(gifter_id)
        giftee_name = santa_service.get_user_name(correct_giftee_id)
        print(f"{gifter_name} -> {giftee_name}")


if __name__ == '__main__':
    test_1()
