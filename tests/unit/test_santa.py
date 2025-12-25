"""
This test validates the correctness and validity of the RNG.
"""
from omar_bot.services.santa_v2 import SantaService
from omar_bot.config.settings import USERS_DIR
from omar_bot.services.user_service import UserService


_CORRECT_PAIRINGS = {
    231576312: 130266190,
    197127934: 231576312,
    473531951: 197127934,
    156267213: 473531951,
    890008145: 156267213,
    29421735: 890008145,
    813074514: 29421735,
    213607266: 813074514,
    130266190: 213607266,
}


def test_1(year=2025):
    # Generate pairings
    user_service = UserService(users_dir=USERS_DIR)
    santa_service = SantaService(user_service, group_name="santa")
    pairings = santa_service.get_pairings(year=year)

    # Compare to the table
    for gifter_id, giftee_id in pairings.items():
        assert _CORRECT_PAIRINGS[gifter_id] == giftee_id


def test_2(year=2026):
    # Generate pairings
    user_service = UserService(users_dir=USERS_DIR)
    santa_service = SantaService(user_service, group_name="santa")
    pairings = santa_service.get_pairings(year=year)

    # Compare to the table
    print()
    for gifter_id, giftee_id in pairings.items():
        gifter_name = santa_service.get_user_name(gifter_id)
        giftee_name = santa_service.get_user_name(giftee_id)
        print(f" {gifter_name} -> {giftee_name}")


if __name__ == '__main__':
    test_1()
    test_2()
