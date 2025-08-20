import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from review.models import Review, Reviewer
from main.models import Store

class Command(BaseCommand):
    help = '스토어별 더미 리뷰 데이터를 생성합니다.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("리뷰 더미 데이터 생성을 시작합니다..."))

        # 기존 리뷰 삭제 (선택)
        Review.objects.all().delete()
        Reviewer.objects.all().delete()
        self.stdout.write("기존 리뷰 및 리뷰어 데이터를 삭제했습니다.")

        stores = Store.objects.all()
        if not stores.exists():
            self.stdout.write(self.style.ERROR("스토어가 존재하지 않습니다."))
            return

        sample_reviews = [
            "정말 맛있어요! 다음에 또 올게요.",
            "음식이 조금 짰지만 전반적으로 만족합니다.",
            "서비스가 친절하지 않았어요. 개선 필요.",
            "분위기가 좋아서 친구들과 오기 좋습니다.",
            "가격 대비 양이 적은 편이에요.",
            "주차가 편리해서 좋았습니다.",
            "대기 시간이 너무 길었어요.",
            "직원들이 친절하고 메뉴도 다양합니다."
        ]

        for store in stores:
            # 스토어별로 5~10개의 리뷰 생성
            for _ in range(random.randint(5, 10)):
                # 리뷰어 생성
                reviewer = Reviewer.objects.create(
                    follower=random.randint(0, 1000),
                    reviewCount=random.randint(0, 50),
                    reviewAvg=round(random.uniform(1, 5), 1)
                )

                review = Review.objects.create(
                    storeId=store,
                    reviewer=reviewer,
                    reviewContent=random.choice(sample_reviews),
                    reviewDate=timezone.now(),
                    reviewRate=random.randint(1, 5)
                )

            self.stdout.write(self.style.SUCCESS(f"{store.name} 리뷰 생성 완료"))

        self.stdout.write(self.style.SUCCESS("모든 스토어 리뷰 더미 데이터 생성 완료!"))
