import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import Profile, Search, Visitor, Type, Category, Store, Menu, NewsLetter
from review.models import ReviewAnalysis
from trend.models import Keyword

class Command(BaseCommand):
    help = '더미 스토어 데이터 2개를 생성합니다.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("더미 데이터 생성을 시작합니다..."))

        # 기존 데이터 삭제 (옵션, 필요한 경우에만 사용)
        self.stdout.write("기존 데이터(Search, Store, Profile 등)를 삭제합니다...")
        Search.objects.all().delete()
        NewsLetter.objects.all().delete()
        Menu.objects.all().delete()
        Store.objects.all().delete()
        Category.objects.all().delete()
        Type.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.all().delete()
        Visitor.objects.all().delete()
        # review.ReviewAnalysis와 trend.Keyword 모델도 삭제 필요

        # 1. User와 Profile 생성 (Store에 연결하기 위함)
        self.stdout.write("User와 Profile 데이터를 생성합니다...")
        user1 = User.objects.create_user(username='dummyuser1', password='dummy_password_1234')
        profile1 = Profile.objects.create(
            userId=user1,
            profileName='홍길동',
            profilePhoneNumber='010-1234-5678'
        )

        user2 = User.objects.create_user(username='dummyuser2', password='dummy_password_1234')
        profile2 = Profile.objects.create(
            userId=user2,
            profileName='김철수',
            profilePhoneNumber='010-9876-5432'
        )
        self.stdout.write(self.style.SUCCESS("User와 Profile 생성 완료"))

        # 2. Type과 Category 생성
        self.stdout.write("Type과 Category 데이터를 생성합니다...")
        type_food = Type.objects.create(name='음식점')
        type_cafe = Type.objects.create(name='카페')

        category_korean = Category.objects.create(type=type_food, name='한식')
        category_western = Category.objects.create(type=type_food, name='양식')
        category_coffee = Category.objects.create(type=type_cafe, name='커피')
        self.stdout.write(self.style.SUCCESS("Type과 Category 생성 완료"))
        
        # 3. Visitor 생성 (Store에 연결하기 위함)
        self.stdout.write("Visitor 데이터를 생성합니다...")
        visitor1 = Visitor.objects.create(
            gender='M', 
            age_group=Visitor.AgeGroup.YOUTH, 
            is_foreign=False
        )
        visitor2 = Visitor.objects.create(
            gender='F', 
            age_group=Visitor.AgeGroup.MIDDLE, 
            is_foreign=True
        )
        self.stdout.write(self.style.SUCCESS("Visitor 생성 완료"))

        # 4. Store 2개 생성
        self.stdout.write("Store 데이터를 2개 생성합니다...")
        store1 = Store.objects.create(
            user=profile1,
            name='우리동네 맛집',
            address='서울 강남구 역삼동 123-45',
            latitude=37.5012,
            longitude=127.0396,
            kakao_place_id=12345,
            type=type_food,
            category=category_korean,
            isWillingCollaborate=True,
            content='유기농 재료로 만든 퓨전 한식 전문점입니다.',
            visitor=visitor1
        )

        store2 = Store.objects.create(
            user=profile2,
            name='힐링 커피하우스',
            address='서울 서초구 서초동 987-65',
            latitude=37.4950,
            longitude=127.0270,
            kakao_place_id=54321,
            type=type_cafe,
            category=category_coffee,
            isWillingCollaborate=False,
            content='조용하고 아늑한 분위기에서 즐기는 스페셜티 커피.',
            visitor=visitor2
        )
        self.stdout.write(self.style.SUCCESS("Store 2개 생성 완료"))

        # 5. Menu 생성 (Store에 연결)
        self.stdout.write("Menu 데이터를 생성합니다...")
        Menu.objects.create(store=store1, name='특제 김치찜', price=15000)
        Menu.objects.create(store=store1, name='한우 불고기 정식', price=25000)
        Menu.objects.create(store=store2, name='아메리카노', price=4500)
        Menu.objects.create(store=store2, name='수제 카라멜 마끼아또', price=6000)
        self.stdout.write(self.style.SUCCESS("Menu 생성 완료"))

        self.stdout.write(self.style.SUCCESS("모든 더미 데이터 생성이 완료되었습니다."))