from fastapi import APIRouter, Request

router = APIRouter(prefix='/debug', tags=['Debug'])


@router.post('/echo')
async def get_echo(request: Request) -> dict:
    """Echo request body.

    For development purposes.
    """
    return await request.json()


@router.get('/crash')
async def get_crash() -> dict[str, str]:
    """Emulate unhandled exeption.

    For development purposes.
    """
    msg = 'you tricked me!'
    raise Exception(msg)
