# set SAMAN2_MERCHANT_ID in your project settings

from django.http import HttpRequest
from zeep import Client, Transport
from requests import Session
from django.conf import settings
from django.urls import reverse
from Crypto.Signature import pkcs1_15
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from base64 import b64encode
import logging
from ..models import Payment

name = 'saman2'
display_name = 'سامان'
WEB_SERVICE = 'https://sep2verify.sep.ir:8443/ref-payment/jax/merchantService?wsdl'
VERIFY_SERVICE = "https://verify.sep.ir/payments/referencepayment.asmx?WSDL"

logger = logging.getLogger(__name__)


def create_client(web_service):
    session = Session()
    session.headers = {}
    transport = Transport(session=session)
    transport.session.headers = {}  # DON'T REMOVE THIS LINE.YOU BLOCK FROM SAMAN BANK IF REMOVE THIS LINE
    return Client(web_service, transport=transport)


def redirect_url(payment):
    return "https://sep2.shaparak.ir/_ipgw_//payment/"


def redirect_data(request: HttpRequest, payment):
    return {
        'token': payment.token,
        'language': 'fa'
    }


def merchant_login(client, username, password):
    login = client.service.MerchantLogin(
        param={
            'UserName': username,
            'Password': password
        }
    )
    if login.Result != 'erSucceed':
        logger.error("Login to web service failed. result message: {} ".format(login.Result))
        return None
    return login.SessionId

def merchant_logout(session_id):
    client = create_client(web_service=WEB_SERVICE)
    logout = client.service.MerchantLogout(
        LogoutParam={
            'SessionId': session_id,
        }

    )
    if logout.Result != 'erSucceed':
        logger.error("Logging out from web service failed. \n Please try again.\n Result message: {}".format(logout.Result))


def generate_transaction_data_to_sign(request: HttpRequest, payment):
    merchant_id = getattr(settings, str(name + '_merchant_id').upper(), 'none')
    username = getattr(settings, str(name + '_username').upper(), 'none')
    password = getattr(settings, str(name + '_password').upper(), 'none')
    terminal_id = getattr(settings, str(name + '_terminal_id').upper(), 'none')
    if merchant_id == 'none':
        logger.error('Merchant ID not in settings.\nDefine your merchant id in settings.py as ' + str(name + '_merchant_id').upper())
        return None, None
    if username == 'none':
        logger.error('Username not in settings.\nDefine your login username in settings.py as ' + str(name + '_username').upper())
        return None, None
    if password == 'none':
        logger.error('Password not in settings.\nDefine yourlogin password id in settings.py as ' + str(name + '_password').upper())
        return None, None
    if terminal_id == 'none':
        logger.error('Terminal ID not in settings.\nDefine your terminal id in settings.py as ' + str(name + '_terminal_id').upper())
        return None, None
    client = create_client(WEB_SERVICE)
    logger.error(request.build_absolute_uri(reverse('pardakht:callback_url', args=[payment.slug, name])))
    sign_result = client.service.GenerateTransactionDataToSign(
        param={
            'WSContext': {
                # 'SessionId': session_id,
                'UserId': username,
                'Password': password
            },
            'TransType': 'enGoods',
            'ReserveNum': payment.trace_number,
            'MerchantId': merchant_id,
            'TerminalId': terminal_id,
            'Amount': payment.price * 10,
            'GoodsReferenceID': "328072757117000000000000000139",
            'RedirectUrl': request.build_absolute_uri(reverse('pardakht:callback_url', args=[payment.slug, name]))
        }
    )
    if sign_result.Result != 'erSucceed':
        logger.error('Gateway return error {} , while signing data.'.format(sign_result.Result))
        return None, None
    return sign_result.DataToSign, sign_result.UniqueId


def sign_data(data):
    private_key_path = getattr(settings, str(name + '_private_key_path').upper(), 'none')
    if private_key_path == 'none':
        logger.error(
            'Certificate private key not in settings.\nDefine your private key absolute in settings.py as ' + str(name + '_private_key_path').upper())
        return None
    try:
        with open(private_key_path, "r") as myfile:
            private_key = RSA.importKey(myfile.read())

    except FileNotFoundError:
        logger.error('Path {} for Certificate private key is not valid.\nPlease set correct path to privete.key file'.format(private_key_path))
        return None
    signer = pkcs1_15.new(private_key)
    digest = SHA256.new()
    digest.update(bytes(data, 'utf-8'))
    sig = signer.sign(digest)
    return b64encode(sig)


def get_token(request: HttpRequest, payment):
    data_to_sign, unique_id = generate_transaction_data_to_sign(request, payment)
    if data_to_sign and unique_id:
        signed_data = sign_data(data_to_sign)
        if signed_data is None:
            return None
    else:
        return None
    username = getattr(settings, str(name + '_username').upper(), 'none')
    password = getattr(settings, str(name + '_password').upper(), 'none')
    client = create_client(WEB_SERVICE)
    result = client.service.GenerateSignedDataToken(
        param={
            'WSContext': {
                'SessionId': '',
                'UserId': username,
                'Password': password,
            },
            'Signature': signed_data,
            'UniqueId': unique_id,
        }
    )
    if result.Result != 'erSucceed':
        logger.error('Gateway returned error code {} while requesting for token'.format(sign_result.Result))
        return None
    payment.gateway = name
    payment.save()
    return result.Token


def verify(request, payment):
    username = getattr(settings, str(name + '_username').upper(), 'none')
    password = getattr(settings, str(name + '_password').upper(), 'none')
    if username == 'none':
        logger.error('Username not in settings.\nDefine your login username in settings.py as ' + str(name + '_username').upper())
        return None
    if password == 'none':
        logger.error('Password not in settings.\nDefine yourlogin password id in settings.py as ' + str(name + '_password').upper())
        return None
    if request.POST.get('State') not in ['OK', 'ok']:
        payment.state = payment.STATE_FAILURE
        payment.payment_result = str(request.POST.get('State'))
        payment.save()
        return
    if payment.trace_number != request.POST.get('ResNum'):
        logger.warning('Manipulation')
        return

    ref_number = request.POST.get('RefNum')
    if Payment.objects.filter(ref_number=ref_number).exists():
        payment.state = payment.STATE_FAILURE
        payment.payment_result = 'MANIPULATION'
        payment.save()
        return
    else:
        payment.ref_number = ref_number
        payment.save()

    verify_client = create_client(WEB_SERVICE)
    verify_result = verify_client.service.VerifyMerchantTrans(
        param={
            'WSContext': {
                'UserId': username,
                'Password': password,
            },
            'Token': payment.token,
            'RefNum': payment.ref_number,
        }
    )
    if verify_result.Result != 'erSucceed':
        logger.error('Gateway returned error code {} while verifeing payment {}'.format(verify_result.Result, payment.trace_number))
        return None
    if verify_result.Amount == 10 * payment.price:
        payment.state = payment.STATE_SUCCESS
    else:
        payment.state = payment.STATE_FAILURE
    payment.verification_result = str(verify_result)
    payment.save()
