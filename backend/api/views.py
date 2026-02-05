from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def test_connexion(request):
    return Response({"message": "✅ Bravo ! Django et React sont connectés !"})