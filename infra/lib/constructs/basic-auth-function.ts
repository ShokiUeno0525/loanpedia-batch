import * as cdk from 'aws-cdk-lib';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import { Construct } from 'constructs';

/**
 * CloudFront Functions用Basic認証のConstruct
 *
 * @remarks
 * このConstructは以下のリソースを作成します：
 * - CloudFront Function（Basic認証）
 *
 * セキュリティに関する注意：
 * - 認証情報はCloudFront Functionコード内に直接記述されています
 * - 本番環境では、より堅牢な認証方式(Cognito等)の使用を検討してください
 */
export class BasicAuthFunction extends Construct {
  /**
   * CloudFront Function
   */
  public readonly function: cloudfront.Function;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    // CloudFront Function コード（認証情報を直接記述）
    const functionCode = `function handler(event) {
  var request = event.request;
  var headers = request.headers;

  // 期待される認証情報（b4KxsVaR:etg5rqKSXU4W をBase64エンコード）
  var expectedAuth = 'Basic YjRLeHNWYVI6ZXRnNXJxS1NYVTRX';

  // Authorizationヘッダーの確認
  if (headers.authorization && headers.authorization.value === expectedAuth) {
    // 認証成功 - リクエストを許可
    return request;
  }

  // 認証失敗 - 401レスポンスを返す
  return {
    statusCode: 401,
    statusDescription: 'Unauthorized',
    headers: {
      'www-authenticate': {
        value: 'Basic realm="Loanpedia Development Environment"'
      },
      'content-type': {
        value: 'text/html; charset=utf-8'
      }
    },
    body: {
      encoding: 'text',
      data: '<!DOCTYPE html><html><head><meta charset="utf-8"><title>401 Unauthorized</title></head><body><h1>401 Unauthorized</h1><p>認証が必要です。</p></body></html>'
    }
  };
}`;

    // CloudFront Functionを作成
    this.function = new cloudfront.Function(this, 'Function', {
      functionName: 'loanpedia-basic-auth',
      code: cloudfront.FunctionCode.fromInline(functionCode),
      runtime: cloudfront.FunctionRuntime.JS_2_0,
      comment: 'Loanpedia Basic認証用CloudFront Function',
    });

    // タグ付け
    cdk.Tags.of(this).add('Component', 'Security');
    cdk.Tags.of(this).add('Purpose', 'BasicAuth');
  }
}
